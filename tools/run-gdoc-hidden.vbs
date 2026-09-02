' 구글 문서 당첨자를 당첨자 시트에 반영 - 창 없이 실행 (작업 스케줄러용).
' 30분마다 이 파일이 실행되어도, gdoc_import 는 이미 있는 당첨자는 건너뛰므로 안전합니다.
Option Explicit
Dim fso, sh, bat
Set fso = CreateObject("Scripting.FileSystemObject")
Set sh  = CreateObject("WScript.Shell")
bat = fso.GetParentFolderName(WScript.ScriptFullName) & "\_gdoc_run.bat"
' 0 = 창 숨김, True = 끝날 때까지 기다림
sh.Run """" & bat & """", 0, True
