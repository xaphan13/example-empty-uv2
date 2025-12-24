from config_log import ConfigLogger

ConfigLogger.setting_path_logger(log_file="empty-uv2.log")

logF = ConfigLogger.get_logger("OnlyFile")
logFC = ConfigLogger.get_logger("FileStdout")

from ex_code_war import main_code_war
from ex_library import main_library
from ex_all_others import main_others
from ex_metaclass import main_metaclass
from ex_file_zip import main_file

# source venv/bin/activate
# venv\Scripts\activate


def main():
    main_metaclass.main_metaclass(0)
    main_code_war.code_war_1(0)

    main_library.main_library(0)
    main_others.main_others(0)
    main_file.run_file_zip()

    logFC.warning(
        "end '-------------------examplePY - main()' '---------------------------------'\n\n\n\n"
        "'*******************************************************************************'"
    )


if __name__ == "__main__":
    main()
