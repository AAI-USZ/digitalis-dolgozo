"""
Exports Issues from a list of specified repository to a CSV file
Credits go to https://gist.github.com/unbracketed/3380407#file-export_repo_issues_to_csv-py for the initial work, but I had to adjust it a bit
FYI: you need to install 'requests' before, best via pip: "$ sudo pip installs requests"
"""
import csv
import requests

REPO = ['eslint/eslint']  # format is username/repo
PERSONAL_TOKEN = '' # Your app token
headers = {'Authorization': 'token %s' % PERSONAL_TOKEN }
params_payload = { 'state' : 'closed', 'since' : '2015-01-01T00:00:00Z' , 'sort' : 'updated'} # Change these parameters based on which issues you are actually searching, see also here: https://developer.github.com/v3/issues/#parameters

def write_issues(response):
    # output a list of issues to csv
    if not r.status_code == 200:
        raise Exception(r.status_code, r.json ())
    for issue in r.json():
        # only proceed, if the issue is no pull requests
        if 'pull_request' not in issue:
            # prepare the information to be used in csv, first labels, then truncate too long body texts
            listlabels = []
            for label in issue["labels"]:
                listlabels.append(label["name"])
            truncatebody = ""
            if issue['body']:
                truncatebody = issue['body'][:10000]
            # now create the csv rows. Decide on your own which information you want to use. Be sure to adjust the header as well
            csvout.writerow([issue['number'], issue['state'].encode('ascii', 'ignore'), issue['title'].encode('ascii', 'ignore'), truncatebody.encode('ascii', 'ignore'), ','.join(listlabels) , issue['created_at'], issue['closed_at']])

i = 0

while (i < len(REPO)):
    ISSUES_FOR_REPO_URL = 'https://api.github.com/repos/%s/issues' % REPO[i]
    print(ISSUES_FOR_REPO_URL)
    r = requests.get(ISSUES_FOR_REPO_URL, params=params_payload, headers=headers)
    print("Starting with Repository: " + REPO[i])

    check = True
    csvfile = '%s-issues.csv' % (REPO[i].replace('/', '-'))

    csvout = csv.writer(open(csvfile, 'w'), delimiter=',', quotechar='"')
    csvout.writerow(['id', 'State' ,'Title', 'Body', 'Labels', 'Created At', 'Closed At']) # This is the header to adjust for a proper csv
    write_issues(r)

    # Check for more pages using the 'Link' header
    if 'Link' in r.headers:
        while check == True:
            # Create overview regarding the different Links, usually previous, first, last and next
            data = {}
            for links in r.headers['Link'].split(","):
                raw = links.split(";")
                data[raw[1][6:6+4]] = raw[0].strip()

            if "next" in data:
                newlink = data["next"][1:-1]
                r = requests.get(newlink, headers=headers)
                print("Now processing page: " + newlink)
                write_issues(r)
                if data["next"] == data["last"]:
                    check = False
                    print("Done with Repository: " + REPO[i])
            else:
                check = False
                print("Done with Repository: " + REPO[i])
    else:
        print("Done with Repository: " + REPO[i])

    i = i + 1
