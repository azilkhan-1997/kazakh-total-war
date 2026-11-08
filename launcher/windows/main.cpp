// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 SAYRAM PLANETA HOLDING contributors.
#ifndef UNICODE
#define UNICODE
#endif
#ifndef _UNICODE
#define _UNICODE
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <algorithm>
#include <cwctype>
#include <sstream>
#include "launcher_core.hpp"

namespace {
const wchar_t* Title = L"KAZAKH TOTAL WAR | SAYRAM PLANETA HOLDING";
struct Failure { int code; std::wstring message; };
struct Handle {
    HANDLE value = INVALID_HANDLE_VALUE;
    explicit Handle(HANDLE h = INVALID_HANDLE_VALUE) : value(h) {}
    ~Handle() { if (value && value != INVALID_HANDLE_VALUE) CloseHandle(value); }
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
};

std::wstring Extended(const std::wstring& path) {
    if (path.rfind(L"\\\\?\\", 0) == 0) return path;
    if (path.rfind(L"\\\\", 0) == 0) return L"\\\\?\\UNC\\" + path.substr(2);
    return L"\\\\?\\" + path;
}
std::wstring ModulePath() {
    for (DWORD count = 512; count <= 32768; count *= 2) {
        std::vector<wchar_t> buffer(count);
        DWORD n = GetModuleFileNameW(nullptr, buffer.data(), count);
        if (!n) throw Failure{10, L"Cannot locate the launcher executable."};
        if (n < count) return std::wstring(buffer.data(), n);
    }
    throw Failure{10, L"The launcher path exceeds the Windows path limit."};
}
std::wstring Directory(const std::wstring& path) {
    size_t slash = path.find_last_of(L"\\/");
    if (slash == std::wstring::npos) throw Failure{10, L"The launcher path has no directory."};
    return path.substr(0, slash);
}
std::string Utf8(const std::wstring& text) {
    if (text.empty()) return {};
    int n = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), nullptr, 0, nullptr, nullptr);
    if (!n) return "[Unicode conversion failed]";
    std::string result(n, '\0');
    WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, text.data(), static_cast<int>(text.size()), result.data(), n, nullptr, nullptr);
    return result;
}
std::wstring Ascii(const std::string& text) { return std::wstring(text.begin(), text.end()); }
std::string JsonString(const std::wstring& text) {
    const char hex[] = "0123456789abcdef";
    std::string result = "\"";
    for (unsigned char c : Utf8(text)) {
        if (c == '\\' || c == '"') { result += '\\'; result += static_cast<char>(c); }
        else if (c < 32) { result += "\\u00"; result += hex[c >> 4]; result += hex[c & 15]; }
        else result += static_cast<char>(c);
    }
    return result + '"';
}
void Report(bool check, int code, const std::wstring& message) {
    if (check) {
        std::string json = "{\"launcher_version\":\"0.3.0\",\"code\":" + std::to_string(code) + ",\"message\":" + JsonString(message) + "}\r\n";
        DWORD written = 0;
        WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), json.data(), static_cast<DWORD>(json.size()), &written, nullptr);
    } else {
        const std::wstring text = L"Не удалось запустить игру / Game could not start.\n\n" + message +
            L"\n\nКод / Code: " + std::to_wstring(code) +
            L"\nСохранения не удалены. / Your saved games have not been deleted.";
        MessageBoxW(nullptr, text.c_str(), Title, MB_OK | MB_ICONERROR);
    }
}
void RequireFile(const std::wstring& path) {
    WIN32_FILE_ATTRIBUTE_DATA info{};
    if (!GetFileAttributesExW(Extended(path).c_str(), GetFileExInfoStandard, &info) ||
        (info.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) || (!info.nFileSizeHigh && !info.nFileSizeLow))
        throw Failure{10, L"Missing or empty required file:\n" + path + L"\n\nExtract the entire Windows game archive, including its runtime folder."};
}
bool HasFile(const std::wstring& path) {
    DWORD attributes = GetFileAttributesW(Extended(path).c_str());
    return attributes != INVALID_FILE_ATTRIBUTES && !(attributes & FILE_ATTRIBUTE_DIRECTORY);
}
void RequireVcRuntime(const std::wstring& root, const std::wstring& engineDirectory) {
    // The authentic R28 Windows binary imports VCRUNTIME140_1.dll but the
    // official installer does not ship that one DLL beside the executable.
    // Check known locations only; never search the working directory/PATH or
    // execute a downloaded prerequisite automatically.
    if (HasFile(engineDirectory + L"\\VCRUNTIME140_1.dll")) return;
    std::vector<wchar_t> system(32768);
    UINT n = GetSystemDirectoryW(system.data(), static_cast<UINT>(system.size()));
    if (n && n < system.size() && HasFile(std::wstring(system.data(), n) + L"\\VCRUNTIME140_1.dll")) return;
    const std::wstring prerequisite = root + L"\\prerequisites\\VC_redist.x64.exe";
    const std::wstring action = HasFile(prerequisite)
        ? L"Run the included Microsoft installer manually, then start the game again:\n" + prerequisite
        : L"Install the official Microsoft Visual C++ 2015-2022 x64 Redistributable, then start the game again.";
    throw Failure{17, L"A Microsoft Visual C++ x64 runtime dependency is missing: VCRUNTIME140_1.dll.\n\n" + action +
        L"\n\nThe launcher does not require administrator rights. The Microsoft installer may ask for them."};
}
std::string ReadSmallFile(const std::wstring& path) {
    Handle file(CreateFileW(Extended(path).c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr));
    LARGE_INTEGER size{};
    if (file.value == INVALID_HANDLE_VALUE || !GetFileSizeEx(file.value, &size) || size.QuadPart <= 0 || size.QuadPart > 65536)
        throw Failure{11, L"Cannot read metadata (maximum 64 KiB):\n" + path};
    std::string data(static_cast<size_t>(size.QuadPart), '\0');
    DWORD count = 0;
    if (!ReadFile(file.value, data.data(), static_cast<DWORD>(data.size()), &count, nullptr) || count != data.size())
        throw Failure{11, L"Incomplete metadata file:\n" + path};
    return data;
}
void RequireAmd64Exe(const std::wstring& path) {
    Handle file(CreateFileW(Extended(path).c_str(), GENERIC_READ, FILE_SHARE_READ, nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr));
    IMAGE_DOS_HEADER dos{}; DWORD count = 0;
    if (file.value == INVALID_HANDLE_VALUE || !ReadFile(file.value, &dos, sizeof(dos), &count, nullptr) ||
        count != sizeof(dos) || dos.e_magic != IMAGE_DOS_SIGNATURE || dos.e_lfanew < 64 || dos.e_lfanew > 1024 * 1024)
        throw Failure{11, L"The bundled engine is not a valid Windows executable:\n" + path};
    LARGE_INTEGER offset{}; offset.QuadPart = dos.e_lfanew;
    IMAGE_NT_HEADERS64 nt{};
    if (!SetFilePointerEx(file.value, offset, nullptr, FILE_BEGIN) || !ReadFile(file.value, &nt, sizeof(nt), &count, nullptr) ||
        count != sizeof(nt) || nt.Signature != IMAGE_NT_SIGNATURE || nt.FileHeader.Machine != IMAGE_FILE_MACHINE_AMD64 ||
        nt.OptionalHeader.Magic != IMAGE_NT_OPTIONAL_HDR64_MAGIC)
        throw Failure{11, L"The game requires the official 64-bit Windows engine. Invalid PE/AMD64 header:\n" + path};
}
void RequireWritableDirectory(const std::wstring& path, bool create) {
    if (create && !CreateDirectoryW(Extended(path).c_str(), nullptr) && GetLastError() != ERROR_ALREADY_EXISTS)
        throw Failure{12, L"Cannot create a portable profile directory:\n" + path + L"\nMove the complete extracted game to a writable folder such as Documents\\Games."};
    // CREATE_NEW cannot overwrite existing files; DELETE_ON_CLOSE removes only this probe.
    const std::wstring probe = path + L"\\.ktw-write-check-" + std::to_wstring(GetCurrentProcessId()) + L"-" + std::to_wstring(GetTickCount64());
    Handle file(CreateFileW(Extended(probe).c_str(), GENERIC_WRITE, 0, nullptr, CREATE_NEW,
        FILE_ATTRIBUTE_TEMPORARY | FILE_FLAG_DELETE_ON_CLOSE, nullptr));
    if (file.value == INVALID_HANDLE_VALUE)
        throw Failure{12, L"The portable game folder is not writable:\n" + path +
            L"\nExtract or move the entire game to Documents\\Games (do not run it inside the archive or Program Files)."};
    char byte = 0; DWORD count = 0;
    if (!WriteFile(file.value, &byte, 1, &count, nullptr) || count != 1)
        throw Failure{12, L"Cannot write game data (check permissions and free disk space):\n" + path};
}
std::wstring WindowsError(DWORD code) {
    wchar_t* buffer = nullptr;
    FormatMessageW(FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_IGNORE_INSERTS,
        nullptr, code, 0, reinterpret_cast<wchar_t*>(&buffer), 0, nullptr);
    std::wstring message = buffer ? buffer : L"No system description available.";
    LocalFree(buffer);
    return L"Windows error " + std::to_wstring(code) + L": " + message;
}
std::wstring MutexName(const std::wstring& path) {
    // One running engine per portable profile. This is not a cryptographic ID.
    uint64_t hash = 14695981039346656037ULL;
    for (wchar_t c : path) { hash ^= static_cast<uint16_t>(std::towlower(c)); hash *= 1099511628211ULL; }
    return L"Local\\SayramPlaneta.KazakhTotalWar." + std::to_wstring(hash);
}
}

int WINAPI wWinMain(HINSTANCE, HINSTANCE, PWSTR, int) {
    bool check = false;
    int argc = 0; LPWSTR* argv = CommandLineToArgvW(GetCommandLineW(), &argc);
    if (argv) {
        for (int i = 1; i < argc; ++i) if (std::wstring(argv[i]) == L"--check") check = true;
        bool valid = argc == 1 || (argc == 2 && check);
        LocalFree(argv);
        if (!valid) { Report(check, 2, L"Supported option: --check (validate the bundle without launching the game)."); return 2; }
    } else { Report(false, 2, L"Cannot parse the command line."); return 2; }
    try {
        const std::wstring root = Directory(ModulePath());
        const std::wstring binaries = root + L"\\runtime\\binaries";
        const std::wstring data = binaries + L"\\data";
        const std::wstring engine = binaries + L"\\system\\pyrogenesis.exe";
        const std::wstring mods = data + L"\\mods";
        const std::wstring game = mods + L"\\kazakh_total_war";
        if (!HasFile(engine))
            throw Failure{10, L"Windows runtime not found:\n" + engine +
                L"\n\nFirst installation: run Setup-Windows.cmd in the game folder. Setup requires installed 64-bit CPython 3.11+ once; playing does not require Python.\nIf this installation was previously completed, a runtime file is missing. Use a new kit directory to reinstall and preserve your existing saves."};
        for (const auto& file : { engine, mods + L"\\public\\mod.json", mods + L"\\public\\public.zip", mods + L"\\mod\\mod.zip",
            game + L"\\mod.json", game + L"\\gui\\page_pregame.xml", game + L"\\maps\\random\\ktw_campaign.js",
            game + L"\\simulation\\components\\KtwController.js" }) RequireFile(file);
        RequireAmd64Exe(engine);
        try { ktw::ValidateMetadata(ReadSmallFile(mods + L"\\public\\mod.json"), ReadSmallFile(game + L"\\mod.json")); }
        catch (const std::exception& e) { throw Failure{11, L"Bundle metadata is incompatible or damaged:\n" + Ascii(e.what())}; }
        RequireVcRuntime(root, binaries + L"\\system");
        RequireWritableDirectory(data, false);
        RequireWritableDirectory(data + L"\\config", true);
        RequireWritableDirectory(data + L"\\cache", true);
        RequireWritableDirectory(data + L"\\saves", true);
        RequireWritableDirectory(binaries + L"\\logs", true);
        if (check) { Report(true, 0, L"Bundle prerequisites and writable portable profile validated. Engine execution has not been tested by --check."); return 0; }
        Handle mutex(CreateMutexW(nullptr, FALSE, MutexName(root).c_str()));
        if (!mutex.value) throw Failure{14, L"Cannot lock the portable profile. " + WindowsError(GetLastError())};
        if (GetLastError() == ERROR_ALREADY_EXISTS) throw Failure{14, L"A game launched from this folder is already running. Close it before launching another copy."};
        std::wstring command = ktw::EngineCommand(engine);
        if (command.size() >= 32767) throw Failure{13, L"The Windows command-line limit was exceeded. Extract the game into a shorter path."};
        STARTUPINFOW startup{}; startup.cb = sizeof(startup);
        PROCESS_INFORMATION process{};
        const std::wstring cwd = binaries + L"\\system";
        if (!CreateProcessW(engine.c_str(), command.data(), nullptr, nullptr, FALSE, 0, nullptr, cwd.c_str(), &startup, &process))
            throw Failure{13, WindowsError(GetLastError()) + L"\n\nEngine: " + engine + L"\nCheck that the entire archive was extracted, including the engine DLLs."};
        Handle child(process.hProcess), thread(process.hThread);
        if (WaitForSingleObject(child.value, INFINITE) != WAIT_OBJECT_0)
            throw Failure{15, L"Failed to wait for the engine process. " + WindowsError(GetLastError())};
        DWORD exitCode = 0;
        if (!GetExitCodeProcess(child.value, &exitCode)) throw Failure{15, L"Cannot retrieve the engine exit status."};
        if (exitCode != 0) {
            std::wostringstream code; code << std::hex << exitCode;
            Report(false, 16, L"The engine exited with status 0x" + code.str() + L".\nDiagnostics: " + binaries + L"\\logs\nThe launcher cannot identify the cause from the exit code alone.");
            return 16;
        }
        return 0;
    } catch (const Failure& failure) { Report(check, failure.code, failure.message); return failure.code; }
    catch (const std::exception& e) { Report(check, 99, L"Unexpected launcher error: " + Ascii(e.what())); return 99; }
}
