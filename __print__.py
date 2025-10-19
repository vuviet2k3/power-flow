# import os, sys
# def icon():
#     print(r"""
#     ██╗   ██╗██╗███████╗████████╗     ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ██╗   ██╗
#     ██║   ██║██║██╔════╝╚══██╔══╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗╚██╗ ██╔╝
#     ██║   ██║██║███████╗   ██║       ██║     ██║   ██║██║  ██║█████╗      ██████╔╝ ╚████╔╝
#     ╚██╗ ██╔╝██║██║  ══╝   ██║       ██║     ██║   ██║██║  ██║██╔══╝      ██╔       ╚██╔╝
#      ╚████╔╝ ██║███████║   ██║       ╚██████╗╚██████╔╝██████╔╝███████╗    ████       ██║
#       ╚═══╝  ╚═╝╚══════╝   ╚═╝        ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═══       ╚═╝
#     """)
#
# def asbtract(io=None):
#     title = sys.stdout.read()
#     if io is None:
#         io = os.path.dirname(__file__)
#     log = os.path.join(io, 'log.txt')
#     with open(log, 'a') as f:
#         f.write(title)
#     print(f'WRITE TO LOG FILE {log}')
#     return


import os, sys, io

def icon():
    print(r"""
    ██╗   ██╗██╗███████╗████████╗     ██████╗ ██████╗ ██████╗ ███████╗    ██████╗ ██╗   ██╗
    ██║   ██║██║██╔════╝╚══██╔══╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔══██╗╚██╗ ██╔╝
    ██║   ██║██║███████╗   ██║       ██║     ██║   ██║██║  ██║█████╗      ██████╔╝ ╚████╔╝ 
    ╚██╗ ██╔╝██║██║  ══╝   ██║       ██║     ██║   ██║██║  ██║██╔══╝      ██╔       ╚██╔╝  
     ╚████╔╝ ██║███████║   ██║       ╚██████╗╚██████╔╝██████╔╝███████╗    ████       ██║   
      ╚═══╝  ╚═╝╚══════╝   ╚═╝        ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═══       ╚═╝   
    """)

def asbtract(io_path=None):
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    # Nội dung bạn muốn ghi vào log
    icon()
    print("Power Flow Started Successfully!")

    # Khôi phục stdout
    sys.stdout = old_stdout

    # Lấy nội dung đã in
    title = buffer.getvalue()

    # Ghi vào file log
    if io_path is None:
        io_path = os.path.dirname(__file__)
    log_file = os.path.join(io_path, 'log.txt')

    with open(log_file, 'a', encoding='utf-8') as f:
        f.writelines(title + "\n")

    print(f"WRITE TO LOG FILE {log_file}")
