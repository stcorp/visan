#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <windows.h>
#include <tchar.h>
#include <fcntl.h>
#include <process.h>

void raise_error(const char *message)
{
    MessageBox(NULL, message, "VISAN ERROR", MB_OK);
    exit(1);
}

int main(int argc, char *argv[])
{
    HMODULE hModule = GetModuleHandleW(NULL);
    char path[MAX_PATH];
    char *command;
    char *envvar;
    char *oldpath;
    const char *pythoncommand = " -c \"from visan.main import main; main()\"";
    GetModuleFileNameA(hModule, path, MAX_PATH);
    size_t path_length = strlen(path);
    size_t command_length;
    size_t env_length;
    int i;

    /* get python path */
    if (path_length < 9 || strcmp(&path[path_length - 9], "visan.exe") != 0)
    {
        raise_error("Application should be named visan.exe");
    }
    path_length -= 9;
    path[path_length] = '\0';
    if (path_length < 8 || strcmp(&path[path_length - 8], "Scripts\\") != 0)
    {
        raise_error("Application should be located in the Scripts directory of a Python installation");
    }
    path_length -= 8;
    strcpy(&path[path_length], "pythonw.exe");
    path_length += 11;

    /* construct python command to launch visan */
    command_length = path_length + strlen(pythoncommand);
    for (i = 1; i < argc; i++)
    {
        command_length += 1 + strlen(argv[i]);
    }

    command = malloc(command_length);
    if (command == NULL)
    {
        raise_error("Commandline too long");
    }
    strcpy(command, path);
    strcat(command, pythoncommand);
    for (i = 1; i < argc; i++)
    {
        strcat(command, " ");
        strcat(command, argv[i]);
    }

    /* set PATH */
    strcpy(&path[path_length - 11], "Library\\bin"); /* path length stays the same! */
    oldpath = getenv("PATH");
    env_length = 5 + path_length;
    if (oldpath != NULL)
    {
        env_length += 1 + strlen(oldpath);
    }
    if ((envvar = (char *)malloc(env_length + 1)) == NULL)
    {
        raise_error("Out of memory error");
    }
    strcpy(envvar, "PATH=");
    strcat(envvar, path);
    if (oldpath != NULL)
    {
        strcat(envvar, ";");
        strcat(envvar, oldpath);
    }
    _putenv(envvar);

    /* launch visan via python */
    DWORD return_value = 0;
    STARTUPINFOA s_info;
    PROCESS_INFORMATION p_info;
    ZeroMemory(&p_info, sizeof(p_info));
    ZeroMemory(&s_info, sizeof(s_info));
    s_info.cb = sizeof(STARTUPINFO);
    if (!CreateProcessA(NULL, command, NULL, NULL, TRUE, 0, NULL, NULL, &s_info, &p_info))
    {
        const char *message = "failed to create process: ";
        char *error;

        error = malloc(strlen(message) + strlen(command));
        strcpy(error, message);
        strcat(error, command);
        raise_error(error);
    }

    /* wait for Python to exit */
    WaitForSingleObject(p_info.hProcess, INFINITE);
    if (!GetExitCodeProcess(p_info.hProcess, &return_value))
    {
        raise_error("failed to get exit code from process");
    }
    return return_value;
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow)
{
    return main(__argc, __argv);
}
