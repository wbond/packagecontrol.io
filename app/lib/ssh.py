import os
import socket

import paramiko


class SSH:
    """
    Represents a simple SSH connection to a server with the intent of executing
    one or more commands should a shell session. Uses SSH agent authentication.
    Does not support password-based auth.

    :ivar client:
        An instance of paramiko.SSHClient

    :ivar shell:
        An instance of paramiko.Channel from paramiko.SSHClient().invoke_shell()

    :param host:
        The hostname to connect to

    :param username:
        The username to connect as
    """

    client = None
    shell = None

    def __init__(self, host, username):
        known_hosts = os.path.expanduser('~/.ssh/known_hosts')

        client = paramiko.SSHClient()

        client.load_host_keys(known_hosts)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(host, username=username, allow_agent=True)

        client.save_host_keys(known_hosts)

        shell = client.invoke_shell()
        shell.settimeout(0.1)

        self.prompt = '>>>> '
        shell.send('PS1="%s"\n' % self.prompt)

        self.client = client
        self.shell = shell

    def close(self):
        """
        Closes the connection to the server
        """

        self.shell.close()
        self.client.close()

    def execute(self, command):
        """
        Executes a shell command and adds a sentinel to the end so we can tell
        when the command is done and can grab the exit code.

        :param command:
            A string command to execute

        :return:
            A tuple of (status_code, output_string)
        """

        # Add an echo command to print the sentinel
        out_sentinel = '\x03\x03'
        exit_sentinel = '\x04\x04'
        sentinel_command = 'echo -e "%s$?%s"\n' % (_escape_byte(out_sentinel), _escape_byte(exit_sentinel))

        self.shell.send(command + '\n' + sentinel_command)

        raw_output = ''
        found_sentinel = False
        while not found_sentinel:
            try:
                raw_output += self.shell.recv(4096).decode('utf-8')
                found_sentinel = raw_output.find('\x04\x04') != -1
            except (socket.timeout):
                pass

        # Clean up newline differences
        raw_output = raw_output.replace("\r\n", "\n")

        # Determine where the sentinels are and parse the output and exit code
        out_sentinel_loc = raw_output.index(out_sentinel)
        exit_sentinel_loc = raw_output.index(exit_sentinel)

        output = raw_output[0:out_sentinel_loc]
        output = output[0:output.rindex(sentinel_command)]
        exit_code = int(raw_output[out_sentinel_loc + len(out_sentinel):exit_sentinel_loc])

        # From the end of the output figure out the prompt so we can strip any
        # leading shell welcome message plus the prompt and the input we wrote to
        # the shell
        prompt = output[output.rindex('\n') + 1:]
        command_input = prompt + command

        # Wrap the input at 80 chars, which is the shell width
        width = 80
        wrapped_parts = [command_input[i:i+width] for i in range(0, len(command_input), width)]
        wrapped_command = ' \r'.join(wrapped_parts)
        wrapped_command_minus_prompt = wrapped_command[len(prompt):]

        try:
            command_input_loc = output.index(wrapped_command) + len(wrapped_command)
        except (ValueError):
            # When the preceeding prompt has already been read, we won't be able
            # to find it, so we look for the command without the prompt. This
            # should always be at 0.
            command_input_loc = output.index(wrapped_command_minus_prompt) + len(wrapped_command_minus_prompt)
        output = output[command_input_loc + 1: -1 - len(prompt)]

        return (exit_code, output)


def _escape_byte(byte):
    return byte.encode('unicode_escape').decode('utf-8')
