#!/usr/bin/env python
import argparse
import subprocess
import platform
import ssl

from cryptography import x509
from cryptography.hazmat.primitives import serialization

def get_os_type() -> str:
    return platform.system()

def generate_cert_bundle_osx(user_provided='') -> str:
    # Read the contents of the system root certificates keychain and system keychain and combine with user provided cert in pem format
    system_root_certificates = subprocess.run(['security', 'find-certificate', '-a', '-p', '/System/Library/Keychains/SystemRootCertificates.keychain'], capture_output=True)
    system_certificates = subprocess.run(['security', 'find-certificate', '-a', '-p', '/Library/Keychains/System.keychain'], capture_output=True)
    cert_bundle = user_provided + system_root_certificates.stdout.decode() + system_certificates.stdout.decode()
    return cert_bundle

def generate_cert_bundle_win(user_provided='') -> str:
    current_root_certs = ssl.enum_certificates("root") # type: ignore
    cert_pem_list = []
    for cert in current_root_certs:
        cert_der = cert[0]
        cert_pem = x509.load_der_x509_certificate(cert_der).public_bytes(encoding=serialization.Encoding.PEM)
        cert_pem_list.append(cert_pem.decode())
    cert_bundle = user_provided + ''.join(cert_pem_list)
    return cert_bundle

def generate_cert_bundle_linux(user_provided='') -> str:
    # Read in contents of cert bundle
    with open('/etc/ssl/certs/ca-certificates.crt', 'r') as f:
        cert_bundle = f.read()
    cert_bundle = user_provided + cert_bundle
    return cert_bundle

def store_cert_bundle(cert_bundle, cert_dir, cert_filename) -> None:
    # Store the combined cert bundle in a file in the cert_dir
    cert_path = cert_dir + cert_filename
    with open(cert_path, 'w') as f:
        f.write(cert_bundle)

def set_ssl_env_nix(cert_dir, cert_filename, shell='zsh') -> None:
    # Store environment zsh / bash profile. 
    if shell == 'zsh':
        print('Writing environment variables to ~/.zshenv')
        profile_file = '~/.zshenv'
    else:
        print('Writing environment variables to ~/.bashrc')
        profile_file = '~/.bashrc'
    # ThisCurrently supports PIP, REQUESTS and HTTPX (likely others as well). WGET, RUBY, OPENSSL, NPM/NODE.JS, 
    env_list = []
    # Cert dir and path to reference in other environment variables
    env_list.append(f'\nexport CERT_PATH={cert_dir + cert_filename}')
    env_list.append(f'\nexport CERT_DIR={cert_dir}')
    # Openssl specific variables - applies to cURL and other openssl apps including -> wget, ruby
    # if wget is not working i may need to look at writing to .wgetrc instead of using env variables (echo "ca_certificate=${CERT_PATH}" >> ~/.wgetrc)
    env_list.append('\nexport SSL_CERT_FILE=${CERT_PATH}')
    env_list.append('\nexport SSL_CERT_DIR=${CERT_DIR}')
    # Python requests specific variables
    env_list.append('\nexport REQUESTS_CA_BUNDLE=${CERT_PATH}')
    # NPM/Node.js specific variables
    env_list.append('\nexport NODE_EXTRA_CA_CERTS=${CERT_PATH}')
    with open(profile_file, 'a') as f:
        f.writelines(env_list)

def set_ssl_env_win(cert_dir, cert_filename) -> None:
    cert_path = cert_dir + cert_filename
    # Openssl specific variables - applies to cURL and other openssl apps including -> wget, ruby
    # if wget is not working i may need to look at writing to .wgetrc instead of using env variables (echo "ca_certificate=${CERT_PATH}" >> ~/.wgetrc)
    subprocess.run(['SETX', 'SSL_CERT_FILE', cert_path, '/m'])
    subprocess.run(['SETX', 'SSL_CERT_DIR', cert_dir, '/m'])
    # Python requests specific variables
    subprocess.run(['SETX', 'REQUESTS_CA_BUNDLE', cert_path, '/m'])
    # NPM/Node.js specific variables
    subprocess.run(['SETX', 'NODE_EXTRA_CA_CERTS', cert_path, '/m'])
    
def check_git_install(cert_dir, cert_filename) -> None:
    check_git = subprocess.run(['git', '--version'], capture_output=True, shell=True)
    if check_git.returncode == 0:
        print('Git is installed, updating cert bundle')
        cert_path = cert_dir + cert_filename
        config_git = subprocess.run(['git', 'config', '--global', 'http.sslcainfo', cert_path])
        if config_git.returncode == 0:
            print('Git SSL config set')
        else:
            print('Git SSL config failed')
    else:
        print('Git is not installed, skipping Git SSL config')
    
def main(user_provided_certs='') -> None:
    sys_type = get_os_type()
    cert_dir = ''
    cert_filename = 'custom-root-bundle.pem'
    if sys_type == 'Darwin':
        print('Mac OS detected')
        cert_dir = '/etc/ssl/certs/'
        print('Generating cert bundle')
        cert_bundle = generate_cert_bundle_osx(user_provided_certs)
        print('Storing cert bundle')
        store_cert_bundle(cert_bundle, cert_dir, cert_filename)
        print('Storing SSL environment variables')
        set_ssl_env_nix(cert_dir, cert_filename, shell='zsh')
    elif sys_type == 'Linux':
        print('Linux OS detected')
        cert_dir = '/etc/ssl/certs/'
        print('Generating cert bundle')
        cert_bundle = generate_cert_bundle_linux(user_provided_certs)
        print('Storing cert bundle')
        store_cert_bundle(cert_bundle, cert_dir, cert_filename)
        print('Storing SSL environment variables')
        set_ssl_env_nix(cert_dir, cert_filename, shell='bash')
    elif sys_type == 'Windows':
        print('Windows OS detected')
        cert_dir = 'C:\\Windows\\System32\\drivers\\etc\\'
        print('Generating cert bundle')
        cert_bundle = generate_cert_bundle_win(user_provided_certs)
        print('Storing cert bundle')
        store_cert_bundle(cert_bundle, cert_dir, cert_filename)
        print('Storing SSL environment variables')
        set_ssl_env_win(cert_dir, cert_filename)
    else:
        print('Unsupported OS detected')
        
    print('Checking Git installation')
    check_git_install(cert_dir, cert_filename)

if __name__ == '__main__':
    user_provided_certs = ''
    argParser = argparse.ArgumentParser(prog='config_ssl.py',
                    description='''This utility will automatically configure a custom root bundle and configure various tools to utilise this
                    root bundle in ssl transactions. Tools covered include GIT, cURL, Python/PIP, Node/NPM''',
                    epilog='''
                    Platform detection is automatic (Win, Linux, OSX). The tool will collect current root certs from the default platform store. 
                    A PEM file can optionally be provided containing additional certificates to combine with the system roots when creating the new custom bundle.
                    When providing a custom PEM file ensure a new line is included at the start and end of the file and between each cert.
                    This script will need to be run as sudo / Administrator''')
    argParser.add_argument("--cert_file", "-c", default='', type=str, help="PEM formatted cert file to combine with system root certs")
    args = argParser.parse_args()
    user_provided_certs = args.cert_file
    main(user_provided_certs)