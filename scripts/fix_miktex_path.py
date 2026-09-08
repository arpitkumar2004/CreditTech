import winreg

def fix_path():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
    val, typ = winreg.QueryValueEx(key, "Path")
    parts = [p.strip() for p in val.split(";") if p.strip()]

    # Filter out file paths like python.exe
    cleaned = [p for p in parts if not p.lower().endswith(".exe") and not p.lower().endswith(".exe\\")]

    miktex_bin = r"C:\Users\RDRL\AppData\Local\Programs\MiKTeX\miktex\bin\x64"
    if miktex_bin not in cleaned:
        cleaned.append(miktex_bin)

    new_val = ";".join(cleaned)
    winreg.SetValueEx(key, "Path", 0, typ, new_val)
    print(f"Successfully updated user PATH in registry. New entries count: {len(cleaned)}")

if __name__ == "__main__":
    fix_path()
