'''
API for backup current directory to kenney/mobile docker hub repo with
dated tag
'''

import datetime
import uuid
import os
import sys
import papermill as pm

timestamp=datetime.date.today().strftime("%Y%m%d%H%sb")
UUID_STR=str(uuid.uuid1())[0:7]


# default feature flags
INCR_EXPERIMENTAL=False
DEBUG=False
RESTORE=False
DEP_NEED=False


def sync_mobile(dir_name, usern="", passw=""):
    '''
        DESCRIPTION: sync latest to the current dated tag
        PARAM: dir_list is list of directorys under Desktop
               gs://.../.. can be used instead if upload output to
               s3
    '''
    if INCR_EXPERIMENTAL:
        d_lower = dir_name.lower()
        # match backup helper convention
        tag_name ="%s-%s" % (d_lower, timestamp)

        status = os.system('''
                    docker login -u {user} --password {dpass};
                    docker tag kenney/{tname} kenney/mobile:{tname};
                    docker tag kenney/{tname} kenney/mobile:{tdir}-latest;
                    docker push kenney/mobile:{tname} && docker push kenney/mobile:{tdir}-latest;
                    '''.format(tname=tag_name, tdir=d_lower, user=usern, dpass=passw))
        if DEBUG:
            print('%s has status %d: done' % (tag_name, status))
        assert status == 0, "failed"


def backup(dir_list, is_full=False, generate=False, user="", passw=""):
    '''
        DESCRIPTION: backups the dir_lists and upload to docker
        PARAM: dir_list is list of directorys under Desktop
               gs://.../.. can be used instead if upload output to
               s3
        EXCEPTIONS: throw exception up to caller if unexpected
    '''
    for d_name in dir_list:
        uuid_str=str(uuid.uuid1())[0:7]
        output="output_%s_run_backup_%s.ipynb" % (timestamp, uuid_str)
        try:
            notebook = pm.execute_notebook("BackupHelper.ipynb",
                                output,
                                {
                                 "USER": user,
                                 "PASS": passw,
                                 "DIR": d_name,
                                 "DEBUG": False,
                                 "FULL": is_full,
                                 "GEN": generate,
                                 "progress_bar": True,
                                 "log_output": True,
                                 "report_mode": True,
                                }
                               )
            print(notebook)
        except pm.PapermillExecutionError:
            print("failed to run %s" %(d_name))
            if DEBUG:
                print(uuid_str, '=>', output)
                print(str(notebook))

            sys.exit(1)
        print('%s is done' % (d_name))

        sync_mobile(d_name)


def restore(dir_dict, user="", passw=""):
    '''
        DESCRIPTION: restores the dir_lists and upload to docker
               assuming all directories are made to be public
        PARAM: dir_dict is dictionary of directory name with tags
               under Desktop
               gs://.../.. can be used instead if upload output to
               s3
    '''
    for dir_name, tag in dir_dict.items():
        uuid_str=str(uuid.uuid1())[0:7]
        output="output_%s_run_restore_%s.ipynb" % (timestamp, uuid_str)
        try:
            notebook = pm.execute_notebook("RestoreBackup.ipynb",
                                output,
                                {
                                 "USER": user,
                                 "PASS": passw,
                                 "DIR": dir,
                                 "TAG": tag,
                                 "DEBUG": True}
                               )
        except pm.PapermillExecutionError:
            print("failed to run %s" %(dir_name))
            if DEBUG:
                print(uuid_str, '=>', output)
                print(str(notebook))
            sys.exit(1)


def cleanup():
    '''
        DESCRIPTION: cleanup pyc, .DS_Store, __pycache__ files and
               prune all images unused
        PARAM: None
    '''
    status = os.system(r'''
                find . -iname \*pyc -exec rm {} \;
                find . -iname .DS_Store -exec rm {} \;
                find . -iname __pycache__ -exec rmdir {} \;
                docker system prune -af;
                ''')
    assert status == 0, "failed"


def backup_incre(dir_list, user="", passw=""):
    '''
        DESCRIPTION: use docker-compose to do incremental and faster
                backup.  Must have INCR_EXPERIMENTAL as True to
                speedup. Uses latest tag to speed up
        PARAM: None
        RETURN: if success returns 0, otherwise non-zero
    '''
    try:
        backup(dir_list, is_full=False, generate=True, user=user, passw=passw)
    except pm.PapermillException as err:
        print(str(err))
        return -1
    return 0


def widget_run_default_backup(pos, blist):
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
