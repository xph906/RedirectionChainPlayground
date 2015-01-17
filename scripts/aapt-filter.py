import argparse, sys
sys.path.append('..')
import plg.metadata

def aaptFilter(sha1, path, output):
    if plg.metadata.is_invalid(path):
        with open(output, 'a') as f:
            f.write('Invalid app: %s\n' % sha1)
    else:
        try:
            metainfo = plg.metadata.getmetadata(path)
            with open(output, 'a') as f:
                f.write('Get metadata successfully app: %s\n' % sha1)
        except Exception as e:
            with open(output, 'a') as f:
                f.write('Get metadata failed app: %s\n' % sha1)
            

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('APPLIST', help='list of apps')
    parser.add_argument('--output', help='output file')
    args = parser.parse_args()
    
    for line in open(args.APPLIST):
        sha1, path = line.strip().split('\t')
        aaptFilter(sha1, path, args.output)

if __name__ == '__main__':
    main()
