import os
import subprocess


################################################################################################
# Service DTO

class ServiceDTO:
    # Class Constructor
    def __init__(self, port, name, description):
        self.description = description
        self.port = port
        self.name = name


#################################################################################################
# Utils Functions


separator_single_line = '------------------------------------------------------------'
separator_double_line = '============================================================'


report_path = '/reports/'



def print_red(text): print("\033[91m {}\033[00m".format (text))

def print_green(text): print("\033[92m {}\033[00m".format (text))

def print_yellow(text): print("\033[93m {}\033[00m".format (text))

def save_results(results, folder_name, file_name):
    try:
        
        file_name_path = folder_name + "/" + file_name

        
        if not os.path.isdir (folder_name):
            os.mkdir (folder_name)

        
        file_to_save = open (file_name_path, 'w')
       
        results = results.encode ('utf-8')
        
        file_to_save.write (results)
        
        file_to_save.close ()
    except Exception, e:
        exception_message = str (e)
        print_red ('[!] Error: Cannot save the results to a file! Reason:\r\n' + exception_message)



def execute_cmd(tool_name, cmd):
    start_msg = "[+] Starting %s ..." % tool_name
    print_green (start_msg)
    
    output = ''

    try:
      
        cmd = cmd.rstrip()
        output += subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)      
        output += '\r\n'
    except Exception, e:
        exception_message = str (e)
        output += exception_message
        print_red ("[!] Error executing the command: " + cmd + " Reason:\r\n" + exception_message)
        output += '\r\n'

    output += separator_single_line + '\r\n'

    end_msg = "[+] Finished %s ..." % tool_name
    print_green (end_msg)
    return output


def error_execution(tool_name): print_red ("Error Executing " + tool_name)


##################################################################################################
# FTP Enum

nmap_ftp_tool_name = 'NMAP FTP Enum'

def execute_nmap_ftp_enum(ip_address, port_number):
    command = "nmap -sV -p %s --script=ftp* %s" % (port_number, ip_address)
    return execute_cmd (nmap_ftp_tool_name, command)


def enum_ftp(ip_address, port_number):
    output = ''
    try:
        nmap_output = execute_nmap_ftp_enum (ip_address, port_number)
        output += nmap_output
    except:
        error_execution (nmap_ftp_tool_name)

    return output


##################################################################################################
# HTTP Enum

nmap_tool_name = 'NMAP HTTP Enum'
crawler_tool_name = 'Gobuster'


def execute_nmap_http_enum(ip_address, port_number):
    command = "nmap -sV -p %s --script=http-enum,http-vuln*  %s" % (port_number, ip_address)
    return execute_cmd (nmap_tool_name, command)


def execute_directories_http_enum(ip_address, port_number):
    command = "gobuster -u http://%s:%s -w /usr/share/wordlists/dirb/common.txt -s '200,204,301,302,307,403,500' -e" % (
        ip_address, port_number)
    return execute_cmd (crawler_tool_name, command)


def enum_http(ip_address, port_number):
    output = ''
    try:
        nmap_output = execute_nmap_http_enum (ip_address, port_number)
        output += nmap_output
    except:
        error_execution (nmap_tool_name)

    try:
        gobuster_output = execute_directories_http_enum (ip_address, port_number)
        output += gobuster_output
    except:
        error_execution (crawler_tool_name)

    return output


##################################################################################################
# Automate Core

def parse_nmap_output(nmap_output):
    service_names_list = {}
    nmap_output = nmap_output.split ("\n")
    for output_line in nmap_output:
        output_line = output_line.strip ()
        services_list = []
        
        if ("tcp" in output_line) and ("open" in output_line) and not ("Discovered" in output_line):
            
            while "  " in output_line:
                output_line = output_line.replace ("  ", " ")
            
            output_line_split = output_line.split (" ")
            
            service_name = output_line_split[2]
           
            port_number = output_line_split[0]

            
            output_line_split_length = len (output_line_split)
            end_position = output_line_split_length - 1
            current_position = 3
            service_description = ''

            while current_position <= end_position:
                service_description += ' ' + output_line_split[current_position]
                current_position += 1

           
            service = ServiceDTO (port_number, service_name, service_description)
          
            if service_name in service_names_list:
               
                services_list = service_names_list[service_name]

            services_list.append (service)
            service_names_list[service_name] = services_list

    return service_names_list


def start_enumeration_process(nmap_output_services_list, ip_address):
    enum_output = ''
    for service_name in nmap_output_services_list:
        services = nmap_output_services_list[service_name]
        if service_name == "http":
            for service in services:
                port_number = service.port.split("/")[0]
                enum_output += enum_http(ip_address,port_number)
        elif "ftp" in service_name:
            for service in services:
                port_number = service.port.split ("/")[0]
                enum_output += enum_ftp(ip_address,port_number)

    save_results(enum_output,'./reports', ip_address+".txt")


def start_nmap_tcp_scan(ip_address):
    nmap_tcp_command = "nmap -T4 -sS -sV -sC -p- -O --open --osscan-guess --version-all %s" % ip_address
    nmap_tcp_output = execute_cmd ('Nmap TCP Scan', nmap_tcp_command)
    
    service_names_list = parse_nmap_output(nmap_tcp_output)
    
    start_enumeration_process(service_names_list,ip_address)
    print_yellow("[!] The Program Scanner Has Finished The Execution (report saved to /reports)")


def main():
    print 'Welcome to PowerScan Let\'s Start'
    print separator_double_line
    print 'What is the IP address that you want to scan:'
    ip_address = raw_input ("IP>")
    print separator_double_line
    start_nmap_tcp_scan (ip_address)
    print separator_double_line


if __name__ == '__main__':
    main ()
