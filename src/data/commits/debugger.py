from datetime import datetime


def debug(msg, error=None):
    now = datetime.now()
    with open(f'D:\sed\jsDB\log_{now.strftime("%Y_%m_%d")}.txt', mode='a', encoding='utf-8') as debug_file:  # ok?
        if error is None:
            debug_file.write(f'INFO {now.strftime("%Y/%m/%d_%H:%M:%S")} - {str(msg)}\n')
            print(f'INFO {now.strftime("%Y/%m/%d_%H:%M:%S")} - {str(msg)}')
        elif error:
            debug_file.write(f'ERROR {now.strftime("%Y/%m/%d_%H:%M:%S")} - {str(msg)}\n')
        else:
            debug_file.write(f'DEBUG {now.strftime("%Y/%m/%d_%H:%M:%S")} - {str(msg)}\n')
