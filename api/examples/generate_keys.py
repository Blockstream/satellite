#!/usr/bin/env python2
"""
Generate RSA key to use for sending data through API
"""
import argparse, gnupg


def main():
    """Generate GPG Keys
    """
    parser = argparse.ArgumentParser(
        description='Generates GPG keys')
    parser.add_argument('-g', '--gnupghome', default=".gnupg",
                        help='GnuPG home directory (default: .gnupg)')
    args        = parser.parse_args()
    gnupghome   = args.gnupghome

    name_real    = raw_input("User name represented by the key: ")
    name_comment = raw_input("Comment to attach to the user name: ")
    name_email   = raw_input("E-mail address: ")

    # GPG object
    gpg = gnupg.GPG(verbose = True, gnupghome = gnupghome)

    # Generate key
    key_params = gpg.gen_key_input(key_type = "RSA", key_length = 1024,
                                   name_real = name_real,
                                   name_comment = name_comment,
                                   name_email = name_email)
    key        = gpg.gen_key(key_params)

    # Export
    public_key  = gpg.export_keys(key.fingerprint)
    private_key = gpg.export_keys(key.fingerprint, True)

if __name__ == '__main__':
    main()

