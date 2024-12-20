import json
import os
import base64
import argparse
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


# RSA Key Management
def load_private_key(private_key_path):
    """
    Load the user's private key from the specified file path.
    """
    with open(private_key_path, "rb") as private_file:
        private_key = serialization.load_pem_private_key(
            private_file.read(),
            password=None,
        )
    return private_key


# Hybrid Decryption Function
def hybrid_decrypt(encrypted_package, private_key, user_id):
    """
    Decrypt the AES key and data using the user's private key.
    """
    if user_id not in encrypted_package["encrypted_aes_keys"]:
        raise ValueError(f"No encrypted AES key found for user ID: {user_id}")

    # Decode Base64-encoded AES key
    encrypted_aes_key = base64.b64decode(encrypted_package["encrypted_aes_keys"][user_id])

    # Decrypt AES key with the user's private key
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    # Decode Base64-encoded IV and encrypted data
    iv = base64.b64decode(encrypted_package["iv"])
    encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])

    # Decrypt the data with AES
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    return json.loads(decrypted_data.decode())


# Reconstruct Original Text
def reconstruct_text(anonymized_text, entity_mapping):
    """
    Replace placeholders in the anonymized text with the original entities.
    """
    for placeholder, original in entity_mapping:
        anonymized_text = anonymized_text.replace(placeholder, original)
    return anonymized_text


# Infer User ID
def infer_user_id(private_key_path, public_keys_folder):
    """
    Infer the user ID by matching the private key with a corresponding public key.
    """
    private_key = load_private_key(private_key_path)
    for public_key_path in Path(public_keys_folder).rglob("*.pem"):
        try:
            with open(public_key_path, "rb") as pub_file:
                public_key = serialization.load_pem_public_key(pub_file.read())

                # Compare the modulus (n) of the keys to find a match
                if private_key.private_numbers().public_numbers.n == public_key.public_numbers().n:
                    return public_key_path.stem  # Use the filename without extension as the user_id
        except Exception:
            continue

    raise ValueError("No matching public key found for the provided private key.")


# Process Response Files
def process_response_files(response_folder, output_folder, reconstructed_folder, private_key_path, public_keys_folder):
    """
    Process all files in the response folder (both JSON and TXT),
    decrypt mappings from the output folder, and reconstruct original texts.
    """
    os.makedirs(reconstructed_folder, exist_ok=True)

    # Check if there are files in the response folder
    response_files = list(Path(response_folder).rglob("*"))
    if not response_files:
        print(f"No files found in the '{response_folder}' folder. Please check your input.")
        return

    # Infer the user ID by matching the private key with a corresponding public key
    user_id = infer_user_id(private_key_path, public_keys_folder)

    # Load the user's private key
    private_key = load_private_key(private_key_path)

    for response_file_path in response_files:
        try:
            if response_file_path.suffix == ".json":
                # Process JSON file
                with open(response_file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                anonymized_text = data["anonymized_text"]
                encrypted_mapping = data["encrypted_mapping"]

                # Decrypt entity mapping
                entity_mapping = hybrid_decrypt(encrypted_mapping, private_key, user_id)

                # Reconstruct the original text
                reconstructed_text = reconstruct_text(anonymized_text, entity_mapping)
            elif response_file_path.suffix == ".txt":
                # Process TXT file
                with open(response_file_path, "r", encoding="utf-8") as file:
                    reworked_text = file.read()

                # Find the corresponding mapping file in the output folder
                mapping_file_path = Path(output_folder) / f"{response_file_path.stem}_processed.json"
                if not mapping_file_path.exists():
                    print(f"Mapping file not found for {response_file_path}. Skipping...")
                    continue

                # Load the mapping file
                with open(mapping_file_path, "r", encoding="utf-8") as file:
                    mapping_data = json.load(file)

                encrypted_mapping = mapping_data["encrypted_mapping"]

                # Decrypt entity mapping
                entity_mapping = hybrid_decrypt(encrypted_mapping, private_key, user_id)

                # Reconstruct the original text with the reworked response
                reconstructed_text = reconstruct_text(reworked_text, entity_mapping)
            else:
                print(f"Unsupported file type: {response_file_path}. Skipping...")
                continue

            # Save reconstructed text to the reconstructed folder
            output_file = Path(reconstructed_folder) / f"{response_file_path.stem}_reconstructed.txt"
            with open(output_file, "w", encoding="utf-8") as output:
                output.write(reconstructed_text)

            print(f"Reconstructed text saved to {output_file}")
        except Exception as e:
            print(f"Error processing {response_file_path}: {e}")


if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Deanonymize response files (JSON or TXT).")
    parser.add_argument(
        "--private_key",
        type=str,
        default="private_key.pem",
        help="Path to the private key file (e.g., private_key.pem). Defaults to 'private_key.pem' in the current directory.",
    )
    parser.add_argument(
        "--public_keys_folder",
        type=str,
        default="public_keys",
        help="Folder containing all public keys. Defaults to 'public_keys'.",
    )
    args = parser.parse_args()

    # Static folders
    response_folder = "response"  # Folder with reworked anonymized files
    output_folder = "output"  # Folder containing mapping files
    reconstructed_folder = "reconstructed"  # Folder to save reconstructed files

    # Process files
    process_response_files(response_folder, output_folder, reconstructed_folder, args.private_key, args.public_keys_folder)
