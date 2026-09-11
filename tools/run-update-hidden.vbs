' 끝장전·ASL 경기기록 갱신(구글시트→사이트→배포) - 창 없이 실행 (작업 스케줄러용).
' 시트 내용이 그대로면 배포 단계가 "바뀐 파일 0개"로 아무것도 안 올리므로 자주 돌아도 안전합니다.
' update.py 는 기록이 줄면(시트 사고) 스스로 멈춰서 잘못된 반영을 막습니다.
Option Explicit
Dim fso, sh, bat
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
bat = fso.GetParentFolderName(WScript.ScriptFullName) & "\_update_run.bat"
' 0 = 창 숨김, True = 끝날 때까지 기다림
sh.Run """" & bat & """", 0, True
