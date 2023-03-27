from json import JSONDecodeError
import json
from debugger import debug
import time
from fetcher import get_request
import os


def make_request_trial(url, token, auth=True):
    request = get_request(url, auth, token)
    i = 0
    while not request.ok and i < 3:  # max 3 trials
        i += 1
        if request.status_code == 403:  # limit exceeded, wait...
            json_obj = json.loads(request.content)
            if json_obj.get('message') == 'Repository access blocked':
                debug(f'Repository access blocked: {url}', False)
                break
            else:
                debug('Limit exceeded, waiting for 10 minutes...')
                debug('Detailed error: ' + str(json_obj.get('message')), True)
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
    return request


def fetch_raw(out_folder, year, month, token, language):
    repos_already_processed = []
    if os.path.isfile(f'{out_folder}/{year}-{month}-repos.txt'):
        with open(f'{out_folder}/{year}-{month}-repos.txt', mode='r', encoding='utf-8') as repo_file:
            repos_already_processed = [repo.strip() for repo in repo_file.read().splitlines()]

    ghapi = 'https://api.github.com/search/'
    try:
        repo_request = f'{ghapi}repositories?q=followers:>=1000 stars:>=100 language:{language} pushed:>{year}-{month}-01 is:public&sort=stars&order=desc&per_page=100'
        r = make_request_trial(f'{repo_request}&page=1', token)

        if not r.ok:
            debug(f'Could not fetch repo data for {year}-{month}-01.')
            debug(f'Detailed error: {r.text}', True)
            return

        with open(f'{out_folder}/{year}-{month}.csv', mode='a', encoding='utf-8') as raw_file:
            try:
                json_object = json.loads(r.content.decode('utf-8'))
                total_repo_count = json_object.get("total_count")
                repo_items = json_object.get('items')
                repo_counter = 0
                debug(f'Found {total_repo_count} repositories.')

                while repo_counter < total_repo_count:
                    repo_index = repo_counter % 100
                    if repo_index >= len(repo_items):
                        continue

                    if repo_counter % 100 == 0 and repo_counter < total_repo_count and repo_counter != 0:
                        r = make_request_trial(f'{repo_request}&page={round((repo_counter / 100) + 1)}', token)
                        if r.status_code == 422:
                            debug('Reached the 1000 limit of search...')
                            break
                        repo_items = json.loads(r.content.decode('utf-8')).get('items')
                        debug(f'Processing {repo_counter}th repository of {total_repo_count}.')

                    repo_item = repo_items[repo_index]
                    repo_counter = repo_counter + 1
                    repo = repo_item.get('full_name').strip()

                    if f'{repo_index}/{repo}' in repos_already_processed:
                        debug(f'Skipping repository: {repo_index}/{repo}.')
                        continue
                    else:
                        repos_already_processed.append(f'{repo_index}/{repo}')

                    repo_url = repo_item.get('url')
                    repo_stargazers = repo_item.get('stargazers_count')
                    repo_score = repo_item.get('score')
                    repo_created = repo_item.get('created_at')

                    if not repo or not repo_url or not repo_stargazers or not repo_score or not repo_created:
                        continue

                    n_month = int(month if month[0] != "0" else month[1:])
                    days_in_month = 30 if n_month < 6 and n_month % 2 == 0 else 30 if n_month >= 6 and n_month % 2 != 0 else 31
                    commit_request = f'{ghapi}commits?q=(fix OR solve OR bug OR issue OR problem OR error) repo:{repo} committer-date:{year}-{month}-01..{year}-{month}-{days_in_month} sort:committer-date-desc&per_page=100'
                    r = make_request_trial(f'{commit_request}&page=1', token)

                    if not r.ok:
                        debug(f'Could not fetch commit data between {year}-{month}-01 and {year}-{month}-31.')
                        debug(f'Detailed error: {r.text}', True)
                        continue

                    json_object = json.loads(r.content.decode('utf-8'))
                    total_commit_count = json_object.get("total_count")
                    commit_items = json_object.get('items')
                    commit_counter = 0
                    debug(f'Found {total_commit_count} commits in {repo}.')

                    with open(f'{out_folder}/{year}-{month}-repos.txt', mode='a', encoding='utf-8') as repo_file:
                        repo_file.write(f'{repo_index}/{repo}\n')

                    while commit_counter < total_commit_count:
                        commit_index = commit_counter % 100
                        if commit_index >= len(commit_items):
                            continue

                        commit_item = commit_items[commit_index]
                        commit_counter = commit_counter + 1
                        if commit_counter % 100 == 0:
                            r = make_request_trial(f'{commit_request}&page={commit_counter / 100}', token)
                            commit_items = json.loads(r.content.decode('utf-8')).get('items')
                            debug(f'Processing {commit_counter}th commit of {total_commit_count}.')

                        commit_url = commit_item.get('url')
                        commit_date = commit_item.get('commit').get('committer').get('date')

                        r = make_request_trial(commit_url, token)

                        if not r.ok:
                            debug(f'Could not fetch commit info with the url: {commit_url}.', False)
                            debug(f'Detailed error: {r.text}', True)
                            continue

                        commit = json.loads(r.content.decode('utf-8'))
                        sha = commit.get('sha')
                        msg = commit.get('commit').get('message').replace('\r', '').replace('\n', ' ').replace(',', '')
                        author = commit.get('commit').get('author').get('name')
                        stats = commit.get('stats')
                        parents = commit.get('parents')

                        if not sha or not msg or not author or not stats or not parents:
                            continue

                        for parent in parents:
                            for file in commit.get('files'):
                                filename = file.get('filename')
                                if filename is None or not filename.endswith('.js'):
                                    continue  # not a JavaScript file

                                raw_url = file.get('raw_url')
                                if raw_url is None:
                                    continue

                                before_sha = parent.get('sha')
                                before_raw_url = '/'.join([part if part != sha else before_sha for part in raw_url.split('/')])

                                raw_file.write(f'{repo},{repo_url},{repo_stargazers},{repo_score},{repo_created},{commit_date},'
                                               f'{author},{stats},{filename},{commit_url},{before_raw_url},{raw_url},{msg}\n')

            except JSONDecodeError as e:
                debug(f'Could not decode content as JSON at {year}-{month}.', False)
                debug(f'Detailed error: {str(e)}', True)
            except Exception as e:
                debug(f'Something went wrong at {year}-{month}.', False)
                debug(f'Detailed error: {str(e)}', True)

    except Exception as e:
        debug('Something went wrong while fetching raw commit info, for detailed error see below.', False)
        debug(str(e), True)
    finally:
        debug(f'Fetching raw values has stopped.')


def fetch_before_after(year, month, in_folder, out_folder, token, line_number=0):
    try:
        date = 'UNK'
        if int(month) < 10:
            month = f'0{month}'
        with open(f'{in_folder}/{year}-{month}.csv', mode='r', encoding='utf8') as raw_file:
            for _ in range(line_number):  # skip first line_number lines
                next(raw_file)

            try:
                for line in raw_file:

                    if line_number % 100 == 0:
                        debug(f'{line_number} url processed of {year}/{month}.')
                    line_number += 1

                    start = line.index('{')
                    end = line.index('}')

                    sub = line[start:end].replace(',', ';')

                    line = line[:start] + sub + line[end:]

                    split = line.split(',')
                    repo, repo_url, repo_stargazers, repo_score, repo_created, commit_date, author, stats, filename, commit_url, before_raw_url, raw_url, msg = line.split(',')
                    split = raw_url.split('/')
                    sha = split[-2] + "_" + split[-1]

                    r1 = make_request_trial(raw_url, token)
                    r2 = make_request_trial(before_raw_url, token)

                    if not r1.ok or not r2.ok:
                        debug(f'Could not fetch files from the following urls: {raw_url} or {before_raw_url}', False)
                        continue

                    debug(f'Found js file: {filename}!')

                    sha_path = f'{out_folder}/{sha}'
                    if os.path.isdir(sha_path):
                        continue
                    else:
                        os.mkdir(sha_path)

                    with open(f'{sha_path}/before.js', mode='w', encoding='utf-8') as before_file,\
                            open(f'{sha_path}/after.js', mode='w', encoding='utf-8') as after_file:
                        before_file.write(r2.content.decode('utf8'))
                        after_file.write(r1.content.decode('utf8'))

            except JSONDecodeError as e:
                debug(f'Could not decode {line_number}th row as JSON retrieved from: {commit_url}.', False)
            except Exception as e:
                debug(f'Something went wrong at while processing the {line_number}th row.', False)
                debug(f'Detailed error: {str(e)}', True)
            finally:
                pass
    except Exception as e:
        debug('Something went wrong while fetching raw commit info, for detailed error see below.', False)
        debug(str(e), True)
    finally:
        debug(f'Fetching commits stopped at {date}, line {line_number}.', False)