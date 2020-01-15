import sys
import glob

if __name__ == "__main__":
    path = sys.argv[1]
    files = glob.glob(path+'/*.txt')
    master = ''
    for file in files:
        with open(file) as fin:
            master += fin.read()+'\n'
    with open("out.txt", 'w') as fout:
        fout.write(master)

