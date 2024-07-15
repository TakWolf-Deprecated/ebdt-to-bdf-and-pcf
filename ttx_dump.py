import os
import shutil

from fontTools import ttx

from path_define import build_dir, fonts_dir


def main():
    ttx_dir = build_dir.joinpath('ttx')
    if ttx_dir.exists():
        shutil.rmtree(ttx_dir)
    ttx_dir.mkdir(parents=True)

    ttx.main([
        os.fspath(fonts_dir.joinpath('Zfull-GB.ttf')),
        '-o',
        os.fspath(ttx_dir.joinpath('Zfull-GB.ttx')),
    ])
    ttx.main([
        os.fspath(fonts_dir.joinpath('Zfull-BIG5.ttf')),
        '-o',
        os.fspath(ttx_dir.joinpath('Zfull-BIG5.ttx')),
    ])


if __name__ == '__main__':
    main()
