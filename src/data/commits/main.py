import fetcher
import repo_fetcher
from func_parser import parse_commits
from func_parser import parse_repo_commits
from stats import generate_stats
import argparse
import os

def main():
    args = handle_params()

    raw_folder = args.raw_folder
    commit_folder = args.commit_folder
    file_folder = args.file_folder
    stats_folder = args.stats_folder

    if raw_folder is not None and not os.path.isdir(raw_folder):
        os.mkdir(raw_folder)

    if commit_folder is not None and not os.path.isdir(commit_folder):
        os.mkdir(commit_folder)

    if file_folder is not None and not os.path.isdir(file_folder):
        os.mkdir(file_folder)

    if stats_folder is not None and not os.path.isdir(stats_folder):
        os.mkdir(stats_folder)

    if args.mode == 'raw':
        fetcher.fetch_raw(out_folder=raw_folder, years=[int(args.year)], token=args.gh_token)
    elif args.mode == 'r_raw':
        repo_fetcher.fetch_raw(out_folder=raw_folder, year=args.year, month=args.month, token=args.gh_token, language=args.language)
    elif args.mode == 'b_a':
        fetcher.fetch_before_after(year=str(args.year),
                           month=str(args.month),
                           in_folder=raw_folder,
                           out_folder=commit_folder,
                           line_number=int(args.last_line),
                           token=args.gh_token)
    elif args.mode == 'r_b_a':
        repo_fetcher.fetch_before_after(year=str(args.year),
                           month=str(args.month),
                           in_folder=raw_folder,
                           out_folder=commit_folder,
                           line_number=int(args.last_line),
                           token=args.gh_token)

    elif args.mode == 'stat':
        generate_stats(commit_folder=commit_folder,
                       stats_folder=stats_folder)
    elif args.mode == 'parse':
        parse_commits(commit_folder=commit_folder,
                      file_folder=file_folder,
                      stats_folder=stats_folder,
                      max_idioms=int(args.max_idioms),
                      last_commit=args.last_commit)
    elif args.mode == 'repo_parse':
        parse_repo_commits(commit_folder=commit_folder,
                      file_folder=file_folder,
                      stats_folder=stats_folder,
                      max_idioms=int(args.max_idioms),
                      last_commit=args.last_commit)


def handle_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', required=True, default='b_a', choices=['raw', 'r_b_a', 'b_a', 'parse', 'repo_parse', 'stat', 'r_raw'], help='The mode in which start the script')
    parser.add_argument('-year')
    parser.add_argument('-month')

    parser.add_argument('-rf', '--raw_folder')
    parser.add_argument('-cf', '--commit_folder')
    parser.add_argument('-ff', '--file_folder')
    parser.add_argument('-sf', '--stats_folder')
    parser.add_argument('-ll', '--last_line', default=0)
    parser.add_argument('-lc', '--last_commit')
    parser.add_argument('-mi', '--max_idioms', default=500)
    parser.add_argument('-gt', '--gh_token', default='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')
    parser.add_argument('-l', '--language', default='js')

    return parser.parse_args()


if __name__ == '__main__':
    main()
