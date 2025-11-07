; NSIS Installer Script for Node.js Server Manager
; This script creates a Windows installer for the application

!include "MUI2.nsh"

; Application Information
!define APP_NAME "Node.js Server Manager"
!define APP_VERSION "2.0.0"
!define APP_PUBLISHER "Your Company Name"
!define APP_EXE "main.exe"
!define APP_UNINST "Uninstall.exe"
!define INSTALL_DIR "$LOCALAPPDATA\Programs\${APP_NAME}"

; Build paths - use relative to execution directory (workspace root)
; NSIS is executed from workspace root with: makensis .github\script\installer.nsi
!define WORKSPACE_ROOT "."

; Installer Settings
Name "${APP_NAME}"
OutFile "dist\NodeJS_Server_Manager_Setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKCU "Software\${APP_NAME}" ""
RequestExecutionLevel user

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
; !insertmacro MUI_PAGE_LICENSE "LICENSE.txt"  ; Uncomment if you have a LICENSE.txt file
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Application" SecApp
    SectionIn RO
    
    ; Set output path to the installation directory
    SetOutPath "$INSTDIR"
    
    ; Copy the main executable and all dependencies from Nuitka standalone build
    ; Use workspace root path constructed from script location
    ; Try the expected standalone build path first
    IfFileExists "${WORKSPACE_ROOT}\dist\main.dist\main.exe" 0 copy_alternative
    
    ; File exists, copy from main.dist
    File "${WORKSPACE_ROOT}\dist\main.dist\main.exe"
    ; Copy all DLLs and dependencies from the dist folder (exclude build artifacts)
    File /r /x "*.c" /x "*.o" /x "*.const" /x "*.h" /x "*.txt" /x "*.bat" /x "*.py" /x ".gitignore" /x ".sconsign*" /x "static_src" /x "main.build" "${WORKSPACE_ROOT}\dist\main.dist\*.*"
    Goto copy_done
    
    copy_alternative:
        ; Alternative: if build structure is different, try direct dist path
        IfFileExists "${WORKSPACE_ROOT}\dist\main.exe" 0 copy_error
        File "${WORKSPACE_ROOT}\dist\main.exe"
        ; Copy dependencies but exclude build directory
        File /r /x "main.build" /x "*.c" /x "*.o" /x "*.const" /x "*.h" /x "*.txt" /x "*.bat" /x "*.py" /x ".gitignore" /x ".sconsign*" /x "static_src" "${WORKSPACE_ROOT}\dist\*.*"
        Goto copy_done
    
    copy_error:
        MessageBox MB_OK|MB_ICONSTOP "Error: Build output not found.$\n$\nExpected 'dist\main.dist\main.exe' or 'dist\main.exe'$\n$\nPlease check the Nuitka build completed successfully."
        Abort
    
    copy_done:
    
    ; Create directories for logs and metrics
    CreateDirectory "$INSTDIR\logs"
    CreateDirectory "$INSTDIR\metrics"
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\${APP_UNINST}"
    
    ; Registry entries for Add/Remove Programs (using HKCU since we're installing to AppData)
    WriteRegStr HKCU "Software\${APP_NAME}" "" $INSTDIR
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\${APP_UNINST}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${APP_PUBLISHER}"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "NoRepair" 1
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\${APP_UNINST}"
    
    ; Create Desktop shortcut (optional)
    ; CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd


; Uninstaller Section
Section "Uninstall"
    ; Remove files and directories
    RMDir /r "$INSTDIR"
    
    ; Remove Start Menu shortcuts
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove Desktop shortcut
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKCU "Software\${APP_NAME}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd


