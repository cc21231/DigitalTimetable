; Page license
; Page components
; Page directory
; Page instfiles
; UninstPage uninstConfirm
; UninstPage instfiles

; Section "PDF Conversion"
; 	SetOutPath $INSTDIR
; 	File "build\exe.win-amd64-3.12\TimetableV2_21.exe"
; 	File "README.md"
; SectionEnd

; Section "un.Uninstaller Section"
; SectionEnd


; Var EXE_dir 
; StrCpy $EXE_dir ""

XPStyle On
ManifestDPIAware True
; AutoCloseWindow True

!define /IfNDef VER 0.2.24.5


CRCCheck On
!include "MUI.nsh"
!include "${NSISDIR}\Contrib\Modern UI\System.nsh"

!define VERSION "2.24.5"
!define NAME "Timetable"
!define COMPANY "Connor Bateman"
!define EXE_NAME "TimetableV2_21"
!define PATH "C:\Users\Connor\Documents\GitHub\DigitalTimetable"
!define FILE "${PATH}\dist\Timetable.exe"
!define PDF_FILE "${PATH}\dist\Timetable.exe"

!define MUI_ICON "${PATH}\win_icon2.ico"
!define MUI_UNICON "${PATH}\win_icon2.ico"
!insertmacro MUI_LANGUAGE "English"

!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange-uninstall-nsis.bmp"


!define MUI_FILE "savefile"
!define MUI_BRANDINGTEXT "${NAME} Beta Ver. ${VERSION}"


InstallDir "$AppData\Local\Programs\${NAME}"

;--------------------------------
;Modern UI Configuration

!define MUI_WELCOMEPAGE  
!define MUI_LICENSEPAGE
!define MUI_DIRECTORYPAGE
!define MUI_ABORTWARNING
!define MUI_UNINSTALLER
!define MUI_UNCONFIRMPAGE
!define MUI_FINISHPAGE  



; LoadAndSetImage icons\win_icon2.bmp


; The name of the installer
Name "${NAME}"

; The file to write
!define /math ARCBITS ${NSIS_PTR_SIZE} * 8
OutFile "${NAME}-V${VER}-(${ARCBITS}-bit).exe"

; Request application privileges for Windows Vista and higher
; RequestExecutionLevel admin

; Build Unicode installer
; Unicode True

; The default installation directory
; InstallDir 

; Registry key to check for directory (so if you install again, it will 
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\NSIS_Timetable" "Install_Dir"


VIProductVersion ${VER}
VIAddVersionKey /LANG=0 "FileVersion" "${VER}"
VIAddVersionKey /LANG=0 "Author" "${COMPANY}"
VIAddVersionKey /LANG=0 "LegalCopyright" "${U+00A9} ${COMPANY}"
VIAddVersionKey /LANG=0 "FileDescription" "${NAME}"


;--------------------------------

; Pages

Page license
Page components
Page directory
Page instfiles

UninstPage uninstConfirm
UninstPage instfiles

;--------------------------------


; !insertmacro MUI_SYSTEM

; The stuff to install
Section "Timetable (required)"
	SetDetailsView show
	SetDetailsPrint both
	; SetBrandingImage $PATH\win_icon2.bmp
	SectionIn RO
	
	; Set output path to the installation directory.
	SetOutPath $INSTDIR
	
	; Put file there
	File "${FILE}"
	File "README.md"
	File "widget_image_config.tcl"
	CreateDirectory "$INSTDIR\icons"
	SetOutPath $INSTDIR\icons
	File "${PATH}\icons\*.*"
	SetOutPath $INSTDIR

	; Write the installation path into the registry
	WriteRegStr HKLM SOFTWARE\NSIS_Timetable "Install_Dir" "$INSTDIR"
	
	; Write the uninstall keys for Windows
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "DisplayName" "${NAME}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoModify" 1
	WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}" "NoRepair" 1
	WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

; Optional section (can be disabled by the user)
Section "Start Menu Shortcuts"
	CreateShortcut "$SMPROGRAMS\${NAME}.lnk" "$INSTDIR\${NAME}"
SectionEnd

Section "Desktop Shortcut"
	CreateShortcut "$DESKTOP\${NAME}.lnk" "$INSTDIR\${NAME}"
SectionEnd

Section "PDF Conversion"
	SetOutPath $INSTDIR
	; File "PDF_FILE.exe"
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"
	; Remove registry keys
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NAME}"
	DeleteRegKey HKLM SOFTWARE\NSIS_Timetable

	; Remove files and uninstaller
	Delete $INSTDIR\${EXE_NAME}
	Delete $INSTDIR\uninstall.exe

	; Remove shortcuts, if any
	Delete "$SMPROGRAMS\${NAME}.lnk"
	Delete "$DESKTOP\${NAME}.lnk"

	; Remove directories
	RMDir "$INSTDIR"
SectionEnd
