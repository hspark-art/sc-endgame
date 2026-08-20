#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""삭제 반영 — 구글시트에서 일부러 지운 경기/세트를 사이트에 반영합니다.

평소 갱신(update.py)은 기록이 줄면 '사고일 수 있다'며 멈춥니다.
정말 지우신 게 맞을 때, 이 스크립트(= 9_삭제반영.bat)를 눌러
  1) 무엇이 지워지는지 먼저 보여주고
  2) 정말 반영할지 한 번 더 물어본 뒤
  3) 확인하면 시트대로 사이트를 다시 맞춥니다(update.py --force).

지워진 게 없으면 그냥 평범하게 최신화합니다.
"""
import io
import os
import sys
import subprocess

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
UPDATE = os.path.join(HERE, 'update.py')


def run_update(*args):
    return subprocess.run([sys.executable, UPDATE, *args],
                          cwd=os.path.dirname(HERE))


def main():
    print('=' * 56)
    print(' 삭제 반영 — 시트에서 지운 내용을 사이트에 반영합니다')
    print('=' * 56)
    print('\n먼저 시트를 읽어 무엇이 달라지는지 확인합니다 (아직 아무것도 안 바꿉니다)…\n')

    # 1) 미리보기 — dry-run 결과를 그대로 보여주면서, 삭제 여부도 판단
    try:
        p = subprocess.run([sys.executable, UPDATE, '--dry-run'],
                           cwd=os.path.dirname(HERE),
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
    except Exception as e:
        print('시트 확인 중 오류가 났습니다:', e)
        input('\nEnter 를 누르면 닫힙니다. ')
        return
    out = (p.stdout or '') + (p.stderr or '')
    print(out)

    deleted = ('[사라짐]' in out) or ('줄었' in out) or ('(-' in out)

    if not deleted:
        print('\n지워진 경기/세트가 없습니다 — 반영할 삭제가 없어요.')
        print('(경기를 새로 넣는 등 평소 갱신은 START 나  /갱신  으로 하시면 됩니다.)')
        input('\nEnter 를 누르면 닫힙니다. ')
        return

    # 2) 삭제가 있으면 한 번 더 확인
    print('\n' + '-' * 56)
    print('위 [사라짐] 으로 표시된 것들이 사이트에서도 지워집니다.')
    print('시트에서 일부러 지우신 게 맞습니까?')
    print('  · 맞으면  y  를 치고 Enter (사이트에 반영합니다)')
    print('  · 실수였다면 그냥 Enter (아무것도 바꾸지 않고 닫습니다 —')
    print('    구글시트에서 되살린 뒤 평소처럼 갱신하세요)')
    print('-' * 56)
    try:
        ans = input('반영할까요? (y / Enter): ').strip().lower()
    except EOFError:
        ans = ''
    if ans != 'y':
        print('\n취소했습니다. 아무것도 바꾸지 않았습니다.')
        input('Enter 를 누르면 닫힙니다. ')
        return

    # 3) 반영
    print('\n삭제를 사이트에 반영합니다…\n')
    r = run_update('--force')
    if r.returncode == 0:
        print('\n반영이 끝났습니다 — 사이트가 시트대로 맞춰졌습니다.')
    else:
        print('\n중간에 문제가 있었던 것 같습니다. 위 메시지를 확인해 주세요.')
    input('Enter 를 누르면 닫힙니다. ')


if __name__ == '__main__':
    main()
