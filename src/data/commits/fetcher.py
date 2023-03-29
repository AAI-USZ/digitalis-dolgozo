from json import JSONDecodeError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests
import gzip
import json
from debugger import debug
import os
import time
from datetime import datetime


def get_request(request_url, auth=True, token=''):
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=Retry(connect=4, backoff_factor=0.5))
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    debug(f"Pinging GhAPI: {request_url}", False)
    if auth:
        return session.get(request_url, auth=('token', token))
    else:
        return session.get(request_url)


def make_request_trial(url, token, auth=True):
    request = get_request(url, auth, token)
    i = 0
    while not request.ok and i < 4:  # max 4 trials
        if request.status_code == 403:  # limit exceeded, wait...
            json_obj = json.loads(request.content)
            if json_obj.get('message') == 'Repository access blocked':
                debug(f'Repository access blocked: {url}', False)
                break
            else:
                debug('Limit exceeded, waiting for 10 minutes...')
                debug('Detailed error: ' + str(json_obj.get('message')), False)
                time.sleep(60 * 10)  # 10 minutes
                request = get_request(url, auth, token)
        elif request.status_code == 404:  # the url probably not correct
            debug(f'The specified url probably not correct: {url}', False)
            break
        elif request.status_code == 422:  # no commit for the specified sha
            debug(f'No commit for the specified sha: {url}', False)
            break
        else:
            pass
        i += 1
    return request


def message_is_bug_fix(message):
    return message is not None \
        and ('fix' in message or 'solve' in message
            or 'bug' in message or 'issue' in message
            or 'problem' in message or 'error' in message)


def fetch_raw(out_folder, token, years=range(2021, 2022), months=range(9, 10), days=range(1, 31), hours=range(0, 24)):
    try:
        date = 'UNK'
        for year in years:
            for month in months:
                with open(f'{out_folder}/{year}-{month}.csv', mode='w+', encoding='utf-8') as raw_file:
                    if 0 < month < 10:
                        month = f'0{month}'
                    for day in days:
                        if 0 < day < 10:
                            day = f'0{day}'
                        for hour in hours:
                            date = f'{year}-{month}-{day}-{hour}'

                            debug(f'Fetching data for {date}')

                            r = make_request_trial(f'https://data.gharchive.org/{date}.json.gz', token, False)

                            if not r.ok:
                                debug(f'Could not fetch data for {date}', False)
                                debug(f'Detailed error: {r.text}', True)
                                continue

                            try:
                                contents = gzip.decompress(r.content).decode('utf-8').split('\n')
                            except:
                                continue

                            i = 0
                            for content in contents:
                                if i == len(contents) - 1:
                                    break

                                try:
                                    json_obj = json.loads(content)
                                    i += 1

                                    event_type = json_obj.get('type')
                                    if event_type != 'PushEvent':
                                        continue

                                    payload = json_obj.get('payload')
                                    if payload is not None and 'commits' in payload:
                                        for commit in payload.get('commits'):
                                            message = commit.get('message')
                                            if message_is_bug_fix(message):
                                                msg = message.replace('\r', '').replace('\n', ' ').replace(',', '')
                                                sha = commit.get("sha")
                                                url = commit.get('url')
                                                raw_file.write(f'{date},{event_type},{sha},{msg},{url}\n')

                                    elif payload is not None and 'shas' in payload and 'url' in json_obj:
                                        for commit in payload.get('shas'):
                                            if len(commit) > 1 and message_is_bug_fix(commit[2]):
                                                msg = commit[2].replace('\r', '').replace('\n', ' ').replace(',', '')
                                                sha = commit[0]
                                                repo = '/'.join(json_obj.get('url').split('/')[3:5])
                                                url = f'https://api.github.com/repos/{repo}/commits/{sha}'
                                                raw_file.write(f'{date},{event_type},{sha},{msg},{url}\n')

                                except JSONDecodeError as e:
                                    debug(f'Could not decode {i}th content as JSON at {date}', True)
                                except:
                                    debug(f'Something went wrong at {date}', True)
    except Exception as e:
        debug('Something went wrong while fetching raw commit info, for detailed error see below.', True)
        debug(str(e), True)
    finally:
        debug(f'Fetching raw values stopped at {date}.')


def fetch_before_after(year, month, in_folder, out_folder, token, line_number=0):
    try:
        date = 'UNK'
        with open(f'{in_folder}/{year}-{month}.csv', mode='r', encoding='utf8') as raw_file:
            for _ in range(line_number):  # skip first line_number lines
                next(raw_file)

            for line in raw_file:

                if line_number % 100 == 0:
                    debug(f'{line_number} url processed of {year}/{month}.')
                line_number += 1

                date, event_type, sha, msg, url = line.split(',')
                url = url.replace('\n', '')

                repo_url = '/'.join([part if part != sha and part != 'commits' else '' for part in url.split('/')])[:-2]
                r = make_request_trial(repo_url, token)
                if not r.ok:
                    debug(f'Could not fetch repo data for {repo_url}', False)
                    debug(f'Detailed error: {r.text}', True)
                    continue
                try:
                    json_object = json.loads(r.content.decode('utf-8'))
                    stargazers = json_object.get('stargazers_count') #number of stars
                    no_commits = 0

                    r = make_request_trial(repo_url + '/contributors', token)
                    if not r.ok:
                        debug(f'Could not fetch repo data for {repo_url + "/contributors"}', False)
                        debug(f'Detailed error: {r.text}', True)
                        continue
                    for contributor in json.loads(r.content.decode('utf-8')):
                        no_commits += contributor.get('contributions')

                    r = make_request_trial(repo_url + '/commits', token)
                    if not r.ok:
                        debug(f'Could not fetch repo data for {repo_url + "/commits"}', False)
                        debug(f'Detailed error: {r.text}', True)
                        continue
                    last_commit_date = json.loads(r.content.decode('utf-8'))[0]\
                        .get('commit').get('author').get('date')

                    if stargazers <= 0:
                        debug(f'The current commit ({sha}) was ignored because the low number of stargazers: {stargazers})')
                        continue
                    elif no_commits < 100:
                        debug(f'The current commit ({sha}) was ignored because the low number of commits: {no_commits})')
                        continue
                    elif datetime.strptime(last_commit_date, '%Y-%b-%d') < datetime.strptime('2020-01-01', '%Y-%b-%d'):
                        debug(f'The current commit ({sha}) was ignored because the repo is not maintained (last commit: {last_commit_date})')
                        continue

                except:
                    debug(f'Something went wrong while fetching repo details.', True)
                    continue

                sha_path = f'{out_folder}/{sha}'
                if os.path.isdir(sha_path):
                    continue

                r = make_request_trial(url, token)
                if not r.ok:
                    debug(f'Could not fetch data for {url}', False)
                    debug(f'Detailed error: {r.text}', True)
                    continue

                try:
                    json_object = json.loads(r.content.decode('utf-8'))

                    files = json_object.get('files')
                    parents = json_object.get('parents')
                    if files is None or parents is None or len(parents) == 0:
                        continue

                    j = 0
                    for file in files:

                        filename = file.get('filename')
                        if filename is None or not filename.endswith('.js'):
                            continue   # not a JavaScript file

                        raw_url = file.get('raw_url')
                        if raw_url is None:
                            continue

                        before_sha = parents[0].get('sha')
                        before_raw_url = '/'.join([part if part != sha else before_sha for part in raw_url.split('/')])

                        r1 = make_request_trial(raw_url, token)
                        r2 = make_request_trial(before_raw_url, token)

                        if not r1.ok or not r2.ok:
                            debug(f'Could not fetch files from the following urls: {raw_url} or {before_raw_url}', False)
                            continue

                        debug(f'Found js file: {filename}!')

                        index_path = f'{out_folder}/{sha}/{j}'
                        if not os.path.isdir(sha_path):
                            os.mkdir(sha_path)
                            os.mkdir(index_path)
                        elif not os.path.isdir(index_path):
                            os.mkdir(index_path)

                        with open(f'{index_path}/before.js', mode='w', encoding='utf-8') as before_file,\
                                open(f'{index_path}/after.js', mode='w', encoding='utf-8') as after_file,\
                                open(f'{index_path}/diff', mode='w', encoding='utf-8') as diff_file:
                            before_file.write(r2.content.decode('utf8'))
                            after_file.write(r1.content.decode('utf8'))
                            diff_file.write(file.get('patch'))

                        j += 1

                except JSONDecodeError as e:
                    debug(f'Could not decode {line_number}th row as JSON retrieved from: {url}.', True)
                except:
                    debug(f'Something went wrong at while processing the {line_number}th row.', True)
                finally:
                    pass
    except Exception as e:
        debug('Something went wrong while fetching raw commit info, for detailed error see below.', False)
        debug(str(e), True)
    finally:
        debug(f'Fetching commits stopped at {date}, line {line_number}.')
