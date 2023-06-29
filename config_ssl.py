import subprocess
import platform

def get_os_type():
    return platform.system()

def generate_cert_bundle_osx(user_provided=''):
    # Read the contents of the system root certificates keychain and system keychain and combine with user provided cert in pem format
    system_root_certificates = subprocess.run(['security', 'find-certificate', '-a', '-p', '/System/Library/Keychains/SystemRootCertificates.keychain'], capture_output=True)
    system_certificates = subprocess.run(['security', 'find-certificate', '-a', '-p', '/Library/Keychains/System.keychain'], capture_output=True)
    cert_bundle = user_provided.join([system_root_certificates.stdout.decode(),system_certificates.stdout.decode()])
    return cert_bundle

def store_cert_bundle(cert_bundle, cert_dir, cert_filename):
    # Store the combined cert bundle in a file in the cert_dir
    cert_path = cert_dir + cert_filename
    with open(cert_path, 'w') as f:
        f.write(cert_bundle)

def set_ssl_env(cert_dir, cert_filename):
    # Store environment zsh profile. 
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
    with open('~/.zshenv', 'a') as f:
        f.writelines(env_list)

def set_git_ssl(cert_dir, cert_filename):
    cert_path = cert_dir + cert_filename
    config_git = subprocess.run(['git', 'config', '--global', 'http.sslcainfo', cert_path])
    if config_git.returncode == 0:
        return True
    else:
        return False 
    
def main():
    sys_type = get_os_type()
    cert_dir = ''
    if sys_type == 'Darwin':
        print('Mac OS detected')
        cert_dir = '/etc/ssl/certs/'
        cert_filename = 'custom-root-bundle.pem'
        print('Generating cert bundle')
        cert_bundle = generate_cert_bundle_osx()
        print('Storing cert bundle')
        store_cert_bundle(cert_bundle, cert_dir, cert_filename)
        print('Storing SSL environment variables')
        set_ssl_env(cert_dir, cert_filename)
        print('Checking Git installation')
        check_git = subprocess.run(['git', '--version'], capture_output=True)
        if check_git.returncode == 0:
            print('Git is installed, updating cert bundle')
            git_ssl_config = set_git_ssl(cert_dir, cert_filename)
            if git_ssl_config:
                print('Git SSL config set')
            else:
                print('Git SSL config failed')

if __name__ == '__main__':
    main()