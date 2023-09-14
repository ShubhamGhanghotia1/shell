import os
import cmd
import shlex
import subprocess
import readline
from collections import defaultdict
import signal
import tempfile
import atexit
import glob  
import shutil
import getpass
import paramiko




class CustomShell(cmd.Cmd):
    intro = "Welcome to the Custom Shell. Type 'help' to list commands or 'exit' to quit."
    prompt = "$ "

    def __init__(self):
        super().__init__()
        self.command_history = []
        self.aliases = defaultdict(str)
        self.background_jobs = {}
        self.prompt = self.get_custom_prompt()
        self.history_file = os.path.expanduser("~/.custom_shell_history")
        self.init_history()
        signal.signal(signal.SIGCHLD, self.handle_child_exit)

    def init_history(self):
        """Initialize command history and load previous history if available."""
        readline.set_history_length(1000)
        if os.path.exists(self.history_file):
            try:
                readline.read_history_file(self.history_file)
            except FileNotFoundError:
                pass

    def do_mkdir(self, arg):
        """Create directories."""
        try:
            directory_name = arg
            os.makedirs(directory_name, exist_ok=True)
            print(f"Directory '{directory_name}' created successfully.")
        except Exception as e:
            print(f"Error creating directory: {e}")

    def do_rm(self, arg):
            """Remove files or directories."""
            try:
                item_name = arg
                if os.path.isfile(item_name):
                    os.remove(item_name)
                    print(f"File '{item_name}' removed successfully.")
                elif os.path.isdir(item_name):
                    shutil.rmtree(item_name)
                    print(f"Directory '{item_name}' and its contents removed successfully.")
                else:
                    print(f"'{item_name}' not found.")
            except Exception as e:
                print(f"Error removing '{item_name}': {e}")


    def save_history(self):
        """Save command history to a file."""
        readline.write_history_file(self.history_file)

    def postcmd(self, stop, line):
        """Store the command in history after execution."""
        readline.add_history(line)
        self.command_history.append(line)
        self.save_history()
        return stop

    def run_command(self, args, input_data=None, output_file=None):
        """Run a command with input/output redirection."""
        try:
            stdin = subprocess.PIPE if input_data else None
            stdout = subprocess.PIPE if output_file else None
            stderr = subprocess.PIPE
            with open(output_file, 'w') if output_file else None as out_file:
                process = subprocess.Popen(args, stdin=stdin, stdout=out_file, stderr=stderr, text=True)
                stdout, stderr = process.communicate(input=input_data)
                if process.returncode == 0:
                    print(stdout)
                else:
                    print(f"Command exited with status {process.returncode}")
        except Exception as e:
            print(f"Error: {e}")

    def do_runscript(self, arg):
        """Execute a script file."""
        try:
            with open(arg, 'r') as script_file:
                script_contents = script_file.read()
                script_lines = script_contents.split('\n')
                for line in script_lines:
                    self.onecmd(line)
        except FileNotFoundError:
            print(f"Script file not found: {arg}")
        except Exception as e:
            print(f"Error executing script: {e}")

    def do_setenv(self, arg):
        """Set an environment variable."""
        try:
            name, value = arg.split('=')
            os.environ[name] = value
        except ValueError:
            print("Invalid usage. Use 'setenv name=value'.")

    def do_getenv(self, arg):
        """Get the value of an environment variable."""
        try:
            value = os.environ.get(arg)
            if value is not None:
                print(f"{arg}={value}")
            else:
                print(f"Environment variable '{arg}' not found.")
        except Exception as e:
            print(f"Error: {e}")



    def do_mv(self, arg):
        """Move or rename files and directories."""
        try:
            args = arg.split()
            if len(args) != 2:
                print("Usage: mv <source> <destination>")
                return

            source, destination = args
            if os.path.exists(source):
                if os.path.isfile(source):
                    shutil.move(source, destination)
                    print(f"File '{source}' moved to '{destination}'.")
                elif os.path.isdir(source):
                    shutil.move(source, destination)
                    print(f"Directory '{source}' moved to '{destination}'.")
                else:
                    print(f"'{source}' is not a valid file or directory.")
            else:
                print(f"'{source}' not found.")
        except Exception as e:
            print(f"Error moving '{source}': {e}")

    def do_cp(self, arg):
        """Copy files and directories."""
        try:
            args = arg.split()
            if len(args) != 2:
                print("Usage: cp <source> <destination>")
                return

            source, destination = args
            if os.path.exists(source):
                if os.path.isfile(source):
                    shutil.copy(source, destination)
                    print(f"File '{source}' copied to '{destination}'.")
                elif os.path.isdir(source):
                    shutil.copytree(source, destination)
                    print(f"Directory '{source}' copied to '{destination}'.")
                else:
                    print(f"'{source}' is not a valid file or directory.")
            else:
                print(f"'{source}' not found.")
        except Exception as e:
            print(f"Error copying '{source}': {e}")
              
    def do_find(self, arg):
        """Search for files and directories."""
        try:
            args = arg.split()
            if len(args) != 2:
                print("Usage: find <directory> <name>")
                return

            directory, name = args
            if os.path.exists(directory) and os.path.isdir(directory):
                found = []
                for root, _, files in os.walk(directory):
                    for file in files:
                        if name in file:
                            found.append(os.path.join(root, file))
                if found:
                    print("Found files:")
                    for item in found:
                        print(item)
                else:
                    print(f"No files matching '{name}' found in '{directory}'.")
            else:
                print(f"'{directory}' is not a valid directory.")
        except Exception as e:
            print(f"Error searching in '{directory}': {e}")
    def do_cat(self, arg):
        """Display the contents of a text file."""
        try:
            if not arg:
                print("Usage: cat <file>")
                return

            if os.path.isfile(arg):
                with open(arg, 'r') as file:
                    content = file.read()
                    print(content)
            else:
                print(f"'{arg}' is not a valid file.")
        except Exception as e:
            print(f"Error displaying '{arg}': {e}")

    def do_nano(self, arg):
            """Open a basic text editor (nano) to edit a text file."""
            try:
                if not arg:
                    print("Usage: nano <file>")
                    return

                # Check if the file exists, and if not, create it.
                if not os.path.isfile(arg):
                    with open(arg, 'w') as new_file:
                        new_file.write("")

                # Launch the nano text editor.
                subprocess.run(['nano', arg])
            except Exception as e:
                print(f"Error editing '{arg}' with nano: {e}")

    def do_source(self, arg):
        """Execute commands from a shell script."""
        try:
            if not arg:
                print("Usage: source <script>")
                return

            # Check if the script file exists.
            if not os.path.isfile(arg):
                print(f"Script file not found: {arg}")
                return

            # Read and execute the script file.
            with open(arg, 'r') as script_file:
                script_contents = script_file.read()
                script_lines = script_contents.split('\n')
                for line in script_lines:
                    # Execute each line as a command.
                    self.onecmd(line)
        except Exception as e:
            print(f"Error executing script '{arg}': {e}")

    def do_connect(self, arg):
        """Connect to a remote server via SSH."""
        try:
            # Parse connection details (e.g., hostname, username, password)
            hostname, username, password = arg.split()
            
            # Create an SSH client instance
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the remote server
            ssh_client.connect(hostname, username=username, password=password)
            
            # Store the SSH client for later use (e.g., executing remote commands)
            self.remote_client = ssh_client
            
            print(f"Connected to {hostname}")
        except Exception as e:
            print(f"Error connecting to remote server: {e}")

    def do_remote_exec(self, arg):
        """Execute a command on the remote server."""
        try:
            # Check if a remote connection is established
            if hasattr(self, 'remote_client'):
                stdin, stdout, stderr = self.remote_client.exec_command(arg)
                # Print the output of the remote command
                print(stdout.read().decode('utf-8'))
            else:
                print("Not connected to a remote server. Use 'connect' to establish a connection.")
        except Exception as e:
            print(f"Error executing remote command: {e}")

    def do_disconnect(self, arg):
        """Disconnect from the remote server."""
        try:
            if hasattr(self, 'remote_client'):
                self.remote_client.close()
                del self.remote_client
                print("Disconnected from the remote server.")
            else:
                print("Not connected to a remote server.")
        except Exception as e:
            print(f"Error disconnecting from remote server: {e}")

    def do_archive(self, arg):
        """Create or extract archives (tar or zip)."""
        try:
            args = shlex.split(arg)

            if not args:
                print("Usage: archive [create/extract] <archive> <files/dirs>")
                return

            operation = args[0]
            archive_name = args[1]
            files_to_archive = args[2:]

            if operation == 'create':
                # Create an archive
                if archive_name.endswith('.tar'):
                    command = ['tar', 'czvf', archive_name] + files_to_archive
                elif archive_name.endswith('.zip'):
                    command = ['zip', '-r', archive_name] + files_to_archive
                else:
                    print("Unsupported archive format. Use .tar or .zip")
                    return
            elif operation == 'extract':
                # Extract an archive
                if archive_name.endswith('.tar'):
                    command = ['tar', 'xzvf', archive_name]
                elif archive_name.endswith('.zip'):
                    command = ['unzip', archive_name]
                else:
                    print("Unsupported archive format. Use .tar or .zip")
                    return
            else:
                print("Usage: archive [create/extract] <archive> <files/dirs>")
                return

            subprocess.run(command, text=True)
            print(f"Command executed: {' '.join(command)}")
        except Exception as e:
            print(f"Error: {e}")


    def do_edit(self, arg):
        """Edit a text file using a text editor."""
        try:
            if not arg:
                print("Usage: edit <filename>")
                return

            file_name = arg.strip()
            if not os.path.isfile(file_name):
                print(f"File not found: {file_name}")
                return

            # Use the user's preferred text editor, or 'nano' as a default
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.run([editor, file_name], text=True)
            print(f"File edited with {editor}: {file_name}")
        except Exception as e:
            print(f"Error: {e}")



    def run_piped_commands(self, args):
        """Run piped commands."""
        try:
            # Split the commands based on the pipe character.
            commands = args.split('|')
            output = None

            for cmd in commands:
                cmd = cmd.strip()
                cmd_args = shlex.split(cmd)
                if output:
                    # Use the previous command's output as input.
                    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=output)
                else:
                    # No previous output, start with standard input.
                    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Update the output for the next command.
                output = result.stdout

            print(output)
        except Exception as e:
            print(f"Error running piped commands: {e}")

    

    def do_useradd(self, arg):
        """Add a new user to the system."""
        try:
            # Check if the user is running the shell as root (superuser)
            if os.geteuid() != 0:
                print("Error: You must have superuser privileges to add a new user.")
                return
            
            # Ensure the user provides a username as an argument
            if not arg:
                print("Usage: useradd <username>")
                return

            username = arg.strip()
            # Use the 'useradd' command to add a new user
            result = subprocess.run(['useradd', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                print(f"User '{username}' added successfully.")
            else:
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    def do_userdel(self, arg):
        """Delete a user from the system."""
        try:
            # Check if the user is running the shell as root (superuser)
            if os.geteuid() != 0:
                print("Error: You must have superuser privileges to delete a user.")
                return

            # Ensure the user provides a username as an argument
            if not arg:
                print("Usage: userdel <username>")
                return

            username = arg.strip()
            # Use the 'userdel' command to delete a user
            result = subprocess.run(['userdel', username], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                print(f"User '{username}' deleted successfully.")
            else:
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    def do_groupadd(self, arg):
        """Add a new user group to the system."""
        try:
            # Check if the user is running the shell as root (superuser)
            if os.geteuid() != 0:
                print("Error: You must have superuser privileges to add a user group.")
                return

            # Ensure the user provides a group name as an argument
            if not arg:
                print("Usage: groupadd <groupname>")
                return

            groupname = arg.strip()
            # Use the 'groupadd' command to add a new group
            result = subprocess.run(['groupadd', groupname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                print(f"Group '{groupname}' added successfully.")
            else:
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    def do_groupdel(self, arg):
        """Delete a user group from the system."""
        try:
            # Check if the user is running the shell as root (superuser)
            if os.geteuid() != 0:
                print("Error: You must have superuser privileges to delete a user group.")
                return

            # Ensure the user provides a group name as an argument
            if not arg:
                print("Usage: groupdel <groupname>")
                return

            groupname = arg.strip()
            # Use the 'groupdel' command to delete a group
            result = subprocess.run(['groupdel', groupname], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                print(f"Group '{groupname}' deleted successfully.")
            else:
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")



    def run_piped_commands(self, args):
            """Run piped commands."""
            try:
                commands = args
                output = None
                for cmd in commands:
                    cmd = cmd.strip()
                    cmd_args = shlex.split(cmd)
                    if '|' in cmd_args:
                        # Handle command pipelines
                        left_pipe, right_pipe = cmd_args.index('|'), cmd_args.index('|') + 1
                        left_cmd = cmd_args[:left_pipe]
                        right_cmd = cmd_args[right_pipe:]

                        # Execute the left command and capture its output
                        left_result = subprocess.run(left_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=output)
                        output = left_result.stdout

                        # Execute the right command with the output of the left command as input
                        right_result = subprocess.run(right_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=output)
                        output = right_result.stdout
                    else:
                        # Execute single command
                        if output:
                            result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=output)
                        else:
                            result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                        output = result.stdout

                print(output)
            except Exception as e:
                print(f"Error: {e}")

    def do_runscript(self, arg):
        """Execute a script file."""
        try:
            with open(arg, 'r') as script_file:
                script_contents = script_file.read()
                script_lines = script_contents.split('\n')
                for line in script_lines:
                    # Execute each line of the script
                    self.onecmd(line)
        except FileNotFoundError:
            print(f"Script file not found: {arg}")
        except Exception as e:
            print(f"Error executing script: {e}")





    def precmd(self, line):
        """Expand environment variables before executing a command."""
        for name, value in os.environ.items():
            line = line.replace(f"${name}", value)
        return line

    def do_replay(self, arg):
        """Replay previous commands."""
        try:
            if arg.isdigit():
                num_commands = int(arg)
                for cmd_idx in range(-num_commands, 0):
                    self.onecmd(self.command_history[cmd_idx])
            else:
                print("Invalid usage. Use 'replay <num_commands>' to replay the last <num_commands> commands.")
        except ValueError:
            print("Invalid argument. Use 'replay <num_commands>' to replay the last <num_commands> commands.")

    def do_record(self, arg):
        """Record the session to a file."""
        try:
            with open(arg, 'w') as record_file:
                for cmd_line in self.command_history:
                    record_file.write(cmd_line + '\n')
            print(f"Session recorded to {arg}")
        except Exception as e:
            print(f"Error recording session: {e}")

    def do_help(self, arg):
        """Customize the help message."""
        if arg:
            cmd.Cmd.do_help(self, arg)
        else:
            print("Custom Shell - Available Commands:")
            print("  exit            Exit the shell")
            print("  cd <directory>  Change the current working directory")
            print("  ls [directory]  List files and directories in the current or specified directory")
            print("  tmpfile         Create and work with temporary files")
            print("  whoami          Display the current user's username")
            print("  clear           Clear the screen")
            print("  replay <num_commands>  Replay the last <num_commands> commands")
            print("  record <file>   Record the session to a file")
            print("  grep <pattern> <file>  Search for a pattern in a file")
            print("  date            Display the current date and time")
            print("  ... (Other commands from previous parts)")

    def cleanup_temp_files(self):
        """Clean up temporary files created during the session."""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temporary file {temp_file}: {e}")

    def do_tmpfile(self, arg):
        """Create and work with temporary files."""
        try:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                self.temp_files.append(temp_file.name)
                editor = os.environ.get('EDITOR', 'nano')
                subprocess.call([editor, temp_file.name])
                print(f"Temporary file created: {temp_file.name}")
        except Exception as e:
            print(f"Error creating temporary file: {e}")

    def do_whoami(self, arg):
        """Display the current user's username."""
        username = os.getlogin()
        print(f"Current user: {username}")

    def do_clear(self, arg):
        """Clear the screen."""
        os.system('clear')

    def do_custom_command(self, arg):
        """Add your custom command here."""
        print(f"Executing custom command with argument: {arg}")

    def do_batch(self, arg):
        """Execute a batch script."""
        try:
            with open(arg, 'r') as script_file:
                script_contents = script_file.read()
                script_lines = script_contents.split('\n')
                for line in script_lines:
                    self.onecmd(line)
        except FileNotFoundError:
            print(f"Batch script file not found: {arg}")
        except Exception as e:
            print(f"Error executing batch script: {e}")

    def do_grep(self, arg):
        """Search for a pattern in files."""
        try:
            args = shlex.split(arg)
            if len(args) < 2:
                print("Usage: grep <pattern> <file>")
                return
            pattern = args[0]
            file_name = args[1]
            if not os.path.isfile(file_name):
                print(f"File not found: {file_name}")
                return
            with open(file_name, 'r') as file:
                lines = file.readlines()
                matching_lines = [line for line in lines if pattern in line]
                for matching_line in matching_lines:
                    print(matching_line, end='')
        except Exception as e:
            print(f"Error: {e}")

    def do_date(self, arg):
        """Display the current date and time."""
        try:
            result = subprocess.run(['date'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0:
                print(result.stdout)
            else:
                print(f"Command exited with status {result.returncode}")
        except Exception as e:
            print(f"Error: {e}")

    def do_exit(self, arg):
        """Exit the shell."""
        print("Goodbye!")
        return True
    
    def do_pwd(self, arg):
        """Print the current working directory."""
        current_directory = os.getcwd()
        print(current_directory)

    def get_custom_prompt(self):
        """Get the custom shell prompt from the environment or use a default."""
        custom_prompt = os.environ.get('CUSTOM_SHELL_PROMPT')
        return custom_prompt if custom_prompt else "$ "

    def do_set_prompt(self, arg):
        """Set a custom shell prompt."""
        try:
            if not arg:
                print("Usage: set_prompt <prompt>")
                return

            custom_prompt = arg.strip()
            os.environ['CUSTOM_SHELL_PROMPT'] = custom_prompt
            self.prompt = custom_prompt
        except Exception as e:
            print(f"Error: {e}")



    def do_cd(self, arg):
        """Change the current working directory."""
        try:
            os.chdir(arg)
        except FileNotFoundError:
            print(f"Directory not found: {arg}")
        except Exception as e:
            print(f"Error changing directory: {e}")

    def do_ls(self, arg):
        """List files and directories in the current directory or by pattern."""
        try:
            if arg:
                files = glob.glob(arg)
            else:
                files = os.listdir()
            for item in files:
                print(item)
        except Exception as e:
            print(f"Error listing directory: {e}")

    def default(self, line):
        """Run a system command."""
        try:
            args = shlex.split(line)
            if '&' in args:
                args.remove('&')
                self.run_command_background(args)
            elif '|' in args:
                self.run_piped_commands(args)
            else:
                if args[0] in self.aliases:
                    args[0] = self.aliases[args[0]]
                self.run_command(args)
        except Exception as e:
            print(f"Error: {e}")

    def do_alias(self, arg):
        """Define a command alias."""
        try:
            alias, command = arg.split('=')
            alias = alias.strip()
            command = command.strip()
            self.aliases[alias] = command
        except ValueError:
            print("Invalid alias definition. Use 'alias alias_name=command'.")

    def do_unalias(self, arg):
        """Remove a command alias."""
        if arg in self.aliases:
            del self.aliases[arg]
        else:
            print(f"Alias '{arg}' not found.")

    def do_bg(self, arg):
        """List and manage background jobs."""
        if arg == '':
            self.list_background_jobs()
        else:
            args = shlex.split(arg)
            if len(args) == 1 and args[0].isdigit():
                job_id = int(args[0])
                self.resume_background_job(job_id)
            else:
                print("Invalid usage. Use 'bg' to list background jobs or 'bg <job_id>' to resume a job.")

    def list_background_jobs(self):
        """List background jobs."""
        for job_id, cmd in self.background_jobs.items():
            print(f"[{job_id}] {cmd}")

    def run_command_background(self, args):
        """Run a command in the background."""
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            job_id = len(self.background_jobs) + 1
            self.background_jobs[job_id] = ' '.join(args)
            print(f"Background job {job_id} started.")
        except Exception as e:
            print(f"Error: {e}")

    def run_piped_commands(self, args):
        """Run piped commands."""
        try:
            commands = args
            output = None
            for cmd in commands:
                cmd = cmd.strip()
                cmd_args = shlex.split(cmd)
                if output:
                    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, input=output)
                else:
                    result = subprocess.run(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                output = result.stdout
            print(output)
        except Exception as e:
            print(f"Error: {e}")

    def do_ping(self, arg):
        """Ping a host to check network connectivity."""
        try:
            # Ensure the user provides a host as an argument
            if not arg:
                print("Usage: ping <hostname or IP>")
                return

            host = arg.strip()
            # Use the 'ping' command to check connectivity
            result = subprocess.run(['ping', '-c', '4', host], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                print(f"Ping to {host} successful:")
                print(result.stdout)
            else:
                print(f"Error: {result.stderr.strip()}")
        except Exception as e:
            print(f"Error: {e}")

    def do_ifconfig(self, arg):
        """Display network interface information using 'ifconfig' or 'ip'."""
        try:
            # Use 'ifconfig' or 'ip' command based on availability
            if os.system('ifconfig') == 0:
                os.system('ifconfig')
            elif os.system('ip') == 0:
                os.system('ip addr show')
            else:
                print("Neither 'ifconfig' nor 'ip' command is available.")
        except Exception as e:
            print(f"Error: {e}")

    def do_netstat(self, arg):
        """Display network statistics using 'netstat'."""
        try:
            # Use the 'netstat' command to display network statistics
            os.system('netstat -i')
        except Exception as e:
            print(f"Error: {e}")

    def do_traceroute(self, arg):
        """Trace the route packets take to a destination using 'traceroute' or 'mtr'."""
        try:
            # Use 'traceroute' or 'mtr' command based on availability
            if os.system('traceroute') == 0:
                host = arg.strip()
                os.system(f'traceroute {host}')
            elif os.system('mtr') == 0:
                host = arg.strip()
                os.system(f'mtr {host}')
            else:
                print("Neither 'traceroute' nor 'mtr' command is available.")
        except Exception as e:
            print(f"Error: {e}")

    def do_uname(self, arg):
        """Display system information using 'uname'."""
        try:
            os.system('uname -a')
        except Exception as e:
            print(f"Error: {e}")

    def do_df(self, arg):
        """Display disk space usage using 'df'."""
        try:
            os.system('df -h')
        except Exception as e:
            print(f"Error: {e}")
    
    def do_ps(self, arg):
        """List running processes using 'ps'."""
        try:
            os.system('ps aux')
        except Exception as e:
            print(f"Error: {e}")

    def do_kill(self, arg):
        """Terminate a process using 'kill'."""
        try:
            if not arg:
                print("Usage: kill <process_id>")
                return

            process_id = arg.strip()
            os.system(f'kill {process_id}')
        except Exception as e:
            print(f"Error: {e}")

    def do_who(self, arg):
        """Display information about logged-in users using 'who'."""
        try:
            os.system('who')
        except Exception as e:
            print(f"Error: {e}")

    def do_users(self, arg):
        """Display a list of currently logged-in users using 'users'."""
        try:
            os.system('users')
        except Exception as e:
            print(f"Error: {e}")

    def do_groups(self, arg):
        """Display group memberships for the current user using 'groups'."""
        try:
            os.system('groups')
        except Exception as e:
            print(f"Error: {e}")


    def do_redirect(self, arg):
        """Demonstrate input/output redirection."""
        try:
            # Create and write to a file
            with open('output.txt', 'w') as file:
                file.write("This is some content written to a file.")

            # Redirect input from a file and output to another file
            os.system('cat < input.txt > output.txt')
        except Exception as e:
            print(f"Error: {e}")

    def do_pipeline(self, arg):
        """Demonstrate command pipelines."""
        try:
            # Use a pipeline to count lines in a file
            os.system('cat input.txt | wc -l')
        except Exception as e:
            print(f"Error: {e}")

    def do_shell_script(self, arg):
        """Execute a shell script."""
        try:
            if not arg:
                print("Usage: shell_script <script_name>")
                return

            script_name = arg.strip()
            os.system(f'bash {script_name}')
        except Exception as e:
            print(f"Error: {e}")

    def do_ssh(self, arg):
        """Connect to a remote host via SSH."""
        try:
            # Parse the SSH command-line arguments
            args = shlex.split(arg)

            if len(args) < 2:
                print("Usage: ssh <user@hostname> <command>")
                return

            host = args[0]
            command = ' '.join(args[1:])

            # Create an SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to the remote host
            ssh.connect(host)

            # Execute the remote command
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode('utf-8')

            # Print the remote command's output
            print(output)

            # Close the SSH connection
            ssh.close()
        except Exception as e:
            print(f"Error: {e}")

    def do_git(self, arg):
        """Run Git commands."""
        try:
            args = shlex.split(arg)
            git_command = args[0]

            if git_command == 'init':
                # Initialize a new Git repository
                subprocess.run(['git', 'init'], text=True)
                print("Initialized empty Git repository.")
            elif git_command == 'clone':
                # Clone a remote Git repository
                if len(args) != 2:
                    print("Usage: git clone <repository>")
                    return
                repository = args[1]
                subprocess.run(['git', 'clone', repository], text=True)
                print(f"Cloned repository: {repository}")
            elif git_command == 'add':
                # Stage a file for commit
                if len(args) != 2:
                    print("Usage: git add <file>")
                    return
                file_to_add = args[1]
                subprocess.run(['git', 'add', file_to_add], text=True)
                print(f"Staged '{file_to_add}' for commit.")
            elif git_command == 'commit':
                # Commit staged changes
                if len(args) != 2:
                    print("Usage: git commit -m '<message>'")
                    return
                commit_message = args[1]
                subprocess.run(['git', 'commit', '-m', commit_message], text=True)
                print(f"Committed changes with message: '{commit_message}'")
            elif git_command == 'status':
                # Show Git repository status
                subprocess.run(['git', 'status'], text=True)
            elif git_command == 'push':
                # Push changes to a remote repository
                if len(args) != 3:
                    print("Usage: git push <remote> <branch>")
                    return
                remote = args[1]
                branch = args[2]
                subprocess.run(['git', 'push', remote, branch], text=True)
                print(f"Pushed to remote '{remote}' branch '{branch}'.")
            elif git_command == 'pull':
                # Pull changes from a remote repository
                if len(args) != 3:
                    print("Usage: git pull <remote> <branch>")
                    return
                remote = args[1]
                branch = args[2]
                subprocess.run(['git', 'pull', remote, branch], text=True)
                print(f"Pulled from remote '{remote}' branch '{branch}'.")
            elif git_command == 'remote':
                # Show remote repositories
                subprocess.run(['git', 'remote', '-v'], text=True)
            elif git_command == 'log':
                # Show Git commit log
                subprocess.run(['git', 'log'], text=True)
            elif git_command == 'diff':
                # Show Git diff
                subprocess.run(['git', 'diff'], text=True)
            elif git_command == 'checkout':
                # Checkout a branch or commit
                if len(args) != 2:
                    print("Usage: git checkout <branch/commit>")
                    return
                target = args[1]
                subprocess.run(['git', 'checkout', target], text=True)
                print(f"Checked out: {target}")
            elif git_command == 'branch':
                # List Git branches
                subprocess.run(['git', 'branch'], text=True)
            elif git_command == 'merge':
                # Merge changes from one branch into the current branch
                if len(args) != 2:
                    print("Usage: git merge <branch>")
                    return
                branch_to_merge = args[1]
                subprocess.run(['git', 'merge', branch_to_merge], text=True)
                print(f"Merged changes from '{branch_to_merge}' into the current branch.")
            elif git_command == 'stash':
                # Stash changes
                subprocess.run(['git', 'stash'], text=True)
                print("Stashed changes.")
            elif git_command == 'pop':
                # Apply stashed changes
                subprocess.run(['git', 'stash', 'pop'], text=True)
                print("Applied stashed changes.")
            elif git_command == 'cherry-pick':
                # Cherry-pick a commit
                if len(args) != 2:
                    print("Usage: git cherry-pick <commit>")
                    return
                commit_to_pick = args[1]
                subprocess.run(['git', 'cherry-pick', commit_to_pick], text=True)
                print(f"Cherry-picked commit: {commit_to_pick}")
            elif git_command == 'clean':
                # Clean untracked files
                subprocess.run(['git', 'clean', '-f'], text=True)
                print("Cleaned untracked files.")
            elif git_command == 'fetch':
                # Fetch changes from a remote repository
                if len(args) != 3:
                    print("Usage: git fetch <remote> <branch>")
                    return
                remote = args[1]
                branch = args[2]
                subprocess.run(['git', 'fetch', remote, branch], text=True)
                print(f"Fetched from remote '{remote}' branch '{branch}'.")
            elif git_command == 'reset':
                # Reset the HEAD to a specific commit
                if len(args) != 2:
                    print("Usage: git reset <commit>")
                    return
                commit_to_reset = args[1]
                subprocess.run(['git', 'reset', commit_to_reset], text=True)
                print(f"Reset to commit: {commit_to_reset}")
            elif git_command == 'revert':
                # Revert a commit
                if len(args) != 2:
                    print("Usage: git revert <commit>")
                    return
                commit_to_revert = args[1]
                subprocess.run(['git', 'revert', commit_to_revert], text=True)
                print(f"Reverted commit: {commit_to_revert}")
            else:
                print("Invalid git command. Supported commands: init, clone, add, commit, status, push, pull, remote, log, diff, checkout, branch, merge, stash, pop, cherry-pick, clean, fetch, reset, revert")
        except Exception as e:
            print(f"Error: {e}")


 





    def handle_child_exit(self, signum, frame):
        """Handle child process exit for background jobs."""
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                job_id = None
                for jid, cmd in self.background_jobs.items():
                    if cmd.startswith(' '.join(frame.f_locals['args'])):
                        job_id = jid
                        break
                if job_id is not None:
                    del self.background_jobs[job_id]
                    print(f"Background job {job_id} finished with status {status}")

        except ChildProcessError:
            pass

if __name__ == "__main__":
    CustomShell().cmdloop()
