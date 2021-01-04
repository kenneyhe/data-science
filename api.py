import papermill as pm
import datetime, uuid, os, sys

timestamp=datetime.date.today().strftime("%Y%m%d%H%sb")
uuid_str=str(uuid.uuid1())[0:7]

import ipywidgets as widgets

# default feature flags
INCR_EXPERIMENTAL=False
DEBUG=False
RESTORE=False
DEP_NEED=False

def sync_mobile(dir):
    '''
        DESCRIPTION: sync latest to the current dated tag
        PARAM: dir_list is list of directorys under Desktop
               gs://.../.. can be used instead if upload output to
               s3
    '''    
    if INCR_EXPERIMENTAL:
        dir = dir.lower()
        # match backup helper convention
        TAG_NAME="%s-%s" % (dir, timestamp)

        status = os.system('''
                    docker login -u {user} --password {dpass};
                    docker tag kenney/{tname} kenney/mobile:{tname};
                    docker tag kenney/{tname} kenney/mobile:{tdir}-latest;            
                    docker push kenney/mobile:{tname} && docker push kenney/mobile:{tdir}-latest;         
                    '''.format(tname=TAG_NAME, tdir=dir, user=USER, dpass=PASS))
        if DEBUG:
            print('%s has status %d: done' % (TAG_NAME, status))
        assert status == 0, "failed"


def backup(dir_list, isFull=False, generate=False):
    '''
        DESCRIPTION: backups the dir_lists and upload to docker
        PARAM: dir_list is list of directorys under Desktop
               gs://.../.. can be used instead if upload output to
               s3
        EXCEPTIONS: throw exception up to caller if unexpected
    '''
    for dir in dir_list:
        uuid_str=str(uuid.uuid1())[0:7]
        output="output_%s_run_backup_%s.ipynb" % (timestamp, uuid_str)
        try:
            pm.execute_notebook("BackupHelper.ipynb",
                                output,       
                                {
                                 "USER": USER,                                  
                                 "PASS": PASS,
                                 "DIR": dir,
                                 "DEBUG": False,
                                 "FULL": isFull,
                                 "GEN": generate,
                                 "progress_bar": True,
                                 "log_output": True,
                                 "report_mode": True,
                                }
                               )
        except pm.PapermillExecutionError:
            print("failed to run %s" %(dir))
            if DEBUG:
                print(uuid_str, '=>', output)
            sys.exit(1)
        print('%s is done' % (dir))

        sync_mobile(dir)


def restore(dir_dict):
    '''
        DESCRIPTION: restores the dir_lists and upload to docker
               assuming all directories are made to be public
        PARAM: dir_dict is dictionary of directory name with tags
               under Desktop
               gs://.../.. can be used instead if upload output to
               s3
    '''
    for dir, tag in dir_dict.items():
        uuid_str=str(uuid.uuid1())[0:7]
        output="output_%s_run_restore_%s.ipynb" % (timestamp, uuid_str)
        try:
            pm.execute_notebook("RestoreBackup.ipynb",
                                output,
                                {
                                 "USER": USER,
                                 "PASS": PASS, 
                                 "DIR": dir,
                                 "TAG": tag,
                                 "DEBUG": True}
                               )
        except pm.PapermillExecutionError:
            print("failed to run %s" %(dir))
            if DEBUG:
                print(uuid_str, '=>', output)
            sys.exit(1)
        except:
            print("unknown error")
            sys.exit(1)


def cleanup():
    '''
        DESCRIPTION: cleanup pyc, .DS_Store, __pycache__ files and
               prune all images unused
        PARAM: None   
    '''
    status = os.system('''
                find . -iname \*pyc -exec rm {} \;
                find . -iname .DS_Store -exec rm {} \;
                find . -iname __pycache__ -exec rmdir {} \;
                docker system prune -af;
                ''')
    assert status == 0, "failed"


def backup_incre(dir_list):
    '''
        DESCRIPTION: use docker-compose to do incremental and faster
                backup.  Must have INCR_EXPERIMENTAL as True to 
                speedup. Uses latest tag to speed up
        PARAM: None
        RETURN: if success returns 0, otherwise non-zero
    '''
    try:
        backup(dir_list, isFull=False, generate=True)
    except:
        return -1
    return 0


def widget_run_default_backup(pos):
    '''
        DESCRIPTION: use button to trigger backup from the blist selected
        PARAM: None      
    '''

    selected = blist.trait_values()['value']
    if DEBUG:
        print(selected)
    pos.set_trait('button_style', 'info')
    pos.set_trait('description', 'In progress...') 
    
    if backup_incre(selected) == 0:
        pos.set_trait('button_style', 'success')
        pos.set_trait('description', 'Done')
    else:
        pos.set_trait('button_style', 'danger')
        pos.set_trait('description', 'Failed')
