#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""서버 접속이 막혔을 때, 무엇이 막혔는지 몇 줄로만 알려 줍니다.

    python3 tools/diag_ssh.py

자동 갱신 로그는 길어서 배포 단계의 안내가 한참 위로 묻힙니다. 그래서
실패했을 때만 이 진단을 **맨 끝에** 한 번 더 찍습니다. 값은 안 찍습니다 —
어느 인증을 받는지, 비밀번호가 통하는지만 봅니다.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass

import deploy                                            # noqa: E402


def main():
    cfg = deploy.load_settings()
    print('── 접속 진단 ──────────────────────────────')
    print('  올릴 곳     %s@%s%s' % (cfg['user'], cfg['host'], cfg['remoteDir']))
    ways = deploy.ssh_auth_methods(dict(cfg, proto='sftp', port=22))
    print('  서버가 받는 인증  %s' % (', '.join(ways) or '(없음)'))

    if any(w.startswith('(') for w in ways):
        # 서버에 물어보지도 못한 것과 '비번을 안 받는다'는 전혀 다릅니다.
        print('  판정  서버에 물어보지도 못했습니다 — 여기서는 22번이 막혀 있습니다.')
        print('        (클라우드 작업방에서 돌리면 늘 이렇게 나옵니다. Actions 에서 보세요.)')
        return
    can_pw = 'password' in ways or 'keyboard-interactive' in ways
    if not can_pw:
        print('  판정  이 계정(%s)은 **비밀번호로는 못 들어갑니다.**' % cfg['user'])
        print('        비밀번호를 아무리 고쳐도 안 됩니다. 서버에서 이 계정에')
        print('        비밀번호 로그인을 막아 둔 것입니다(흔한 기본 설정입니다).')
        print('        → 형님께 sshd_config 의 PermitRootLogin·PasswordAuthentication 확인,')
        print('          또는 배포 전용 계정 + SSH 키를 요청하세요. 키가 오면 붙이겠습니다.')
        return
    try:
        import paramiko
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cli.connect(cfg['host'], port=22, username=cfg['user'],
                    password=cfg['password'], timeout=20,
                    look_for_keys=False, allow_agent=False)
        cli.close()
        print('  판정  비밀번호로 들어가집니다 ✅ (그렇다면 막힌 곳은 다른 데입니다)')
    except Exception as e:
        print('  판정  비밀번호 로그인은 받는데 **지금 비밀번호가 다릅니다** (%s).'
              % type(e).__name__)
        print('        → 시크릿 SC_FTP_PASS 에 비밀번호만 다시 붙여넣어 주세요.')
        print('          https://github.com/hspark-art/sc-endgame/settings/secrets/actions')


if __name__ == '__main__':
    main()
