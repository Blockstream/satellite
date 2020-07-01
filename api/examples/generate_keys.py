#!/usr/bin/env python3
"""
Generate RSA key to use for sending data through API
"""
import argparse, gnupg, os, getpass


def main():
    """Generate GPG Keys
    """
    parser = argparse.ArgumentParser(
        description='Generates GPG keys',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-g', '--gnupghome', default=".gnupg",
                        help='GnuPG home directory')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help="Verbose mode")
    args        = parser.parse_args()

    name_real    = input("User name represented by the key: ")
    name_comment = input("Comment to attach to the user name: ")
    name_email   = input("E-mail address: ")

    if (not os.path.exists(args.gnupghome)):
        os.mkdir(args.gnupghome)

    # GPG object
    gpg = gnupg.GPG(verbose = args.verbose, gnupghome = args.gnupghome)

    # Password
    gpg_password = getpass.getpass(prompt='Please enter the passphrase to '
                                   'protect your new key: ')

    # Generate key
    key_params = gpg.gen_key_input(key_type = "RSA", key_length = 1024,
                                   name_real = name_real,
                                   name_comment = name_comment,
                                   name_email = name_email,
                                   passphrase = gpg_password)
    key        = gpg.gen_key(key_params)

    # Export
    public_key  = gpg.export_keys(key.fingerprint)
    private_key = gpg.export_keys(key.fingerprint, True,
                                  passphrase = gpg_password)

    print("Keys generated succesfully at {}".format(
        os.path.abspath(args.gnupghome)))

if __name__ == '__main__':
    main()

