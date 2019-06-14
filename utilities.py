import os
import subprocess

def compress_tarball_gzip(dgstfile, dgstdir): #.gz
    cmd = 'tar -zcvf %s %s' % (dgstfile, dgstdir)
    print('The shell command: %s', cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: exit code: %s; %s###################',
                      dgstdir, e.returncode, e.output)
        return False

    print('process layer_id:%s : gzip compress tar archival, consumed time ==> %f s', dgstdir) #.gz
    return True


def decompress_tarball_gunzip(sf, dgstdir):
    cmd = 'tar -zxf %s -C %s' % (sf, dgstdir)
    print('The shell command: %s', cmd)
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        if "Unexpected EOF in archive" in e.output or "ignored" in e.output:
            print('###################%s: Pass exit code: %s; %s###################',
                      dgstdir, e.returncode, e.output)
        print('###################%s: exit code: %s; %s###################',
                      sf, e.returncode, e.output)
        return False

    print('FINISHED! to ==========> %s', dgstdir)
    return True


def clear_extracting_dir(dir):
    """clear the content"""

    cmd4 = 'rm -rf %s' % (dir+'*')
    print('The shell command: %s', cmd4)
    try:
        subprocess.check_output(cmd4, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: exit code: %s; %s###################',
                      dir, e.returncode, e.output)
        return False

    return True


def mk_dir(newdir):
    cmd1 = 'mkdir -pv {}'.format(quote(newdir))
    try:
        subprocess.check_output(cmd1, stderr=subprocess.STDOUT, shell=True, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print('###################%s: %s###################',
                      newdir, e.output)
        return False
    return True


startup_nodes_hulks = [ #hulks
        {"host": "192.168.0.170", "port": "7000"}, 
        {"host": "192.168.0.170", "port": "7001"},
        
        {"host": "192.168.0.171", "port": "7000"}, 
        {"host": "192.168.0.171", "port": "7001"},
        
        {"host": "192.168.0.172", "port": "7000"}, 
        {"host": "192.168.0.172", "port": "7001"},
        
        {"host": "192.168.0.174", "port": "7000"}, 
        {"host": "192.168.0.174", "port": "7001"},
        
        {"host": "192.168.0.176", "port": "7000"}, 
        {"host": "192.168.0.176", "port": "7001"},
        
        {"host": "192.168.0.177", "port": "7000"}, 
        {"host": "192.168.0.177", "port": "7001"},
        
        {"host": "192.168.0.179", "port": "7000"}, 
        {"host": "192.168.0.179", "port": "7001"},
        
        {"host": "192.168.0.180", "port": "7000"},
        {"host": "192.168.0.180", "port": "7001"}]
        

   
startup_nodes_thors = [ #thors
        {"host": "192.168.0.200", "port": "7000"}, 
        {"host": "192.168.0.200", "port": "7001"},
        
        {"host": "192.168.0.201", "port": "7000"}, 
        {"host": "192.168.0.201", "port": "7001"},
        
        {"host": "192.168.0.202", "port": "7000"}, 
        {"host": "192.168.0.202", "port": "7001"},
        
        {"host": "192.168.0.203", "port": "7000"}, 
        {"host": "192.168.0.203", "port": "7001"},
        
        {"host": "192.168.0.204", "port": "7000"}, 
        {"host": "192.168.0.204", "port": "7001"},
        
        {"host": "192.168.0.205", "port": "7000"}, 
        {"host": "192.168.0.205", "port": "7001"},
        
        {"host": "192.168.0.208", "port": "7000"}, 
        {"host": "192.168.0.208", "port": "7001"},
        
        {"host": "192.168.0.209", "port": "7000"}, 
        {"host": "192.168.0.209", "port": "7001"},
        
        {"host": "192.168.0.210", "port": "7000"},
        {"host": "192.168.0.210", "port": "7001"},
        
        {"host": "192.168.0.211", "port": "7000"}, 
        {"host": "192.168.0.211", "port": "7001"},
        
        {"host": "192.168.0.212", "port": "7000"}, 
        {"host": "192.168.0.212", "port": "7001"},
        
        {"host": "192.168.0.213", "port": "7000"}, 
        {"host": "192.168.0.213", "port": "7001"},
        
        {"host": "192.168.0.214", "port": "7000"}, 
        {"host": "192.168.0.214", "port": "7001"},
        
        {"host": "192.168.0.215", "port": "7000"}, 
        {"host": "192.168.0.215", "port": "7001"},
        
        {"host": "192.168.0.216", "port": "7000"}, 
        {"host": "192.168.0.216", "port": "7001"},
        
        {"host": "192.168.0.217", "port": "7000"}, 
        {"host": "192.168.0.217", "port": "7001"},
        
        {"host": "192.168.0.218", "port": "7000"}, 
        {"host": "192.168.0.218", "port": "7001"},
        
        {"host": "192.168.0.219", "port": "7000"}, 
        {"host": "192.168.0.219", "port": "7001"},
        
        {"host": "192.168.0.221", "port": "7000"}, 
        {"host": "192.168.0.221", "port": "7001"},
        
        {"host": "192.168.0.222", "port": "7000"}, 
        {"host": "192.168.0.222", "port": "7001"},
        
        {"host": "192.168.0.223", "port": "7000"}, 
        {"host": "192.168.0.223", "port": "7001"}]
    
"""
{u'SliceSize': 166, u'DurationCP': 0.000751436, u'DurationCMP': 3.7068e-05, u'ServerIp': u'192.168.0.171', u'DurationML': 0.000553802, u'DurationNTT': 3.7041e-05, u'DurationRS': 0.001379347}  
"""             
    


    



