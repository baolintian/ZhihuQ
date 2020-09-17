# coding=utf-8
import os
import re
def file_name(file_dir):
    for root, dirs, files in os.walk(file_dir):
        return files

def merge_file(directory):

    content = ''
    files = file_name('./'+directory)
    get_flag = False
    real_name = re.split('\\\\', directory)[-1]
    # outfile = open("./merge_result/question/"+real_name+".html", "w+", encoding='utf8')

    for item in files:
        with open("./"+directory+"/"+item, 'r', encoding='utf8') as f:
            lines = f.readlines()
            
            if get_flag == False:
                for i in range(0, len(lines)-2):
                    # outfile.write(lines[i])
                    content += lines[i]
                get_flag = True
            else:
                for i in range(16, len(lines)-2):
                    content += lines[i]
                    # outfile.write(lines[i])
            f.close()
            # os.remove("./"+directory+"/"+item)

    # outfile.write(r"    </body>")
    content += r"    </body>"
    # outfile.write(r"</html>")
    content += r"</html>"
    return content


