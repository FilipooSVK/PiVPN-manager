# PiVPN Manager

PiVPN Manager is a Python application for managing your PiVPN server via SSH. It provides a graphical interface to perform various tasks such as creating connections, removing clients, listing clients, and listing connected clients.

## Features

- **SSH Connection:** Connect to your PiVPN server securely via SSH.
- **Client Management:** Create, remove, and list VPN clients easily.
- **Connection Status:** Check the connection status and list connected clients.
- **User-friendly Interface:** Intuitive graphical interface for easy navigation.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/FilipooSVK/PiVPN-manager.git
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the application:

    ```bash
    python main_alpha_v1.py
    ```

## Usage

1. Launch the application.
2. Enter the IP address of your PiVPN server and click "Connect".
3. Provide SSH credentials when prompted.
4. Once connected, you can perform various tasks using the buttons in the interface:
   - Create Connection: Add a new VPN client.
   - Remove Client: Remove an existing VPN client.
   - List Clients: View a list of all VPN clients.
   - List Connected Clients: View a list of currently connected clients.
5. Exit the application when done.

## Version
current version 1.0

## Contributing

Contributions are welcome! Please feel free to open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
