# Certificate Deployment Tool
This script is designed to set SSL/TLS root certificate configurations for a range of common command line and developer tools on Windows, OSX and Linux systems. The script will collect and bundle all certs from the platforms default root store, create an new single file bundle and set it as the root store for the following applications:
 - GIT
 - Python / PIP / Python Requests
 - wget
 - cURL
 - Node.JS / NPM
 - Ruby
 - Most apps that rely on the OpenSSL cert store configuration

You can optionally supply a PEM formatted certificate bundle to add to the cert bundle that will be created from the platform specific system root certs.
> [!NOTE]
> This script requires administrative / sudo privileges to manage certificate and system settings

> [!IMPORTANT]
> These utilities are not affiliated with, nor supported by Zscaler in any way.

# Usage
Simply run the script from the command line and it will auto detect platform type, collect system root certs and apply appropriate application specific settings.

```bash
./config_ssl.py
```

## Adding Additional Certs
To add additional certs from a PEM formatted file simply specify the cert file using the -c option.

```bash
./config_ssl.py -c additional_certs.pem
```

The supplied file must contain one or more certificates in PEM format, and include a leading and trailing new line. See following example with new line characters highlighted

```text
\n
-----BEGIN CERTIFICATE-----\n
<cert data>\n
-----END CERTIFICATE-----\n
\n
-----BEGIN CERTIFICATE-----\n
<cert data>\n
-----END CERTIFICATE-----\n
\n
```

# Packaging with [PyInstaller](https://pyinstaller.org/)

If required the script can be packaged using PyInstaller to enable running on hosts that do not have python installed locally. PyInstaller will need to be run on the target platform type to generate the single file executable for that platform type.

Quick guide to using PyInstaller - refer to PyInstaller documentation for additional help.

**Install PyInstaller**

```
pip install pyinstaller
```

**Clone Repo**

```
git clone https://github.com/jxg81/dev-tool-cert-loader
```

**Change to Repo Root and Execute PyInstaller**

```
cd dev-tool-cert-loader
pyinstaller -F config_ssl.py
```
**Copy File to Required Host and Execute**

The -F option used in the previous step will create a single file executable named `config_sll` in `../dist` that can be distributed to hosts that require certificate maintenance