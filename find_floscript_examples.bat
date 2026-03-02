@echo off
REM 查找 FloTHERM 2020.2 安装目录中的 FloSCRIPT 示例

echo ==========================================
echo   FloSCRIPT 示例文件查找工具
echo ==========================================
echo.

REM 常见安装路径
set PATHS=
    "C:\Program Files\Siemens\SimcenterFlotherm\2020.2"
    "C:\Program Files\Mentor Graphics\FloTHERM\v2020.2"
    "C:\Program Files (x86)\Mentor Graphics\FloTHERM\v2020.2"
    "C:\Program Files\FloTHERM\v2020.2"
)

for %%p in (%PATHS%) do (
    if exist %%p (
        echo [INFO] 找到安装目录: %%p
        echo.

        REM 查找 FloSCRIPT 示例
        if exist "%%p\examples\FloSCRIPT" (
            echo [FloSCRIPT 示例目录]:
            dir /b "%%p\examples\FloSCRIPT"
            echo.

            REM 查找 Tutorial
            if exist "%%p\examples\FloSCRIPT\Tutorial" (
                echo [Tutorial 目录]:
                dir /b "%%p\examples\FloSCRIPT\Tutorial"
                echo.
            )
        )

        REM 查找 Schema 文档
        if exist "%%p\docs\Schema-Documentation\FloSCRIPT" (
            echo [FloSCRIPT Schema 文档]:
            dir /b "%%p\docs\Schema-Documentation\FloSCRIPT"
            echo.
        )

        REM 查找 FloXML 示例
        if exist "%%p\examples\FloXML" (
            echo [FloXML 示例目录]:
            dir /b "%%p\examples\FloXML"
            echo.
        )
    )
)

echo.
echo ==========================================
echo 请查看上述目录中的 .xml 文件示例
echo 特别是 Tutorial 目录中的 FloSCRIPTv11-Tutorial
echo ==========================================
pause
