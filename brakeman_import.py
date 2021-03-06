import os

from coverity_import import CoverityIssueCollector, main, get_opts, InvalidFormatException

import json

class BrakemanCollector(CoverityIssueCollector):
    _checker_prefix='brakeman'

    '''
    A simple collector for Brakeman reports.
    '''

    def find_line(self, issue):
        return issue['line'] or '1'

    def process(self, f):
        data = json.load(f)
        try:
            data['scan_info']
            data['scan_info']['brakeman_version']
            self._build_dir = data['scan_info']['app_path']
        except Exception, e:
            raise InvalidFormatException("Couldn't find attribute", e)

        # There are also members "ignored_warnings" and "errors"
        for issue in data.get('warnings',[]) + data.get('ignored_warnings',[]):
            # warning_type, warning_code
            # fingerprint
            # message
            # file, line, link
            # code (expression affected)
            # render_path
            # location
            #   type:controller, controller:
            #   type:method, class:, method:
            #   type:model, model:
            #   type:template, template:
            # user_input (affected variable/parameter)
            # confidence

            description = []
            if issue['code']:
               description.append('In expression "%s"' % (issue['code'],))
            if issue['user_input']:
               description.append('"%s" is unsafe' % (issue['user_input'],))
            description = issue['message']+'. '+ ', '.join(description)+'.'

            attrs = {
                'checker': issue['warning_type'],
                'tag': 'Warning',
                'subcategory': issue['confidence'],
                'description': ''.join(description)
            }
            if issue['fingerprint']:
                attrs['extra'] = issue['fingerprint']
            if issue['location'] and issue['location'].get('method',None):
                attrs['function'] = issue['location']['class']+'.'+issue['location']['method']
            if issue['line'] is None:
                issue['line'] = self.find_line(issue)

            msg = self.create_issue(**attrs)

            # Do we need to walk over issue['render_path'] to create
            # dataflow events?
        
            # Also takes description, method, tag
            msg.add_location(
                issue['line'],
                issue['file'],
                link = issue.get('link', None),
                linktext = issue.get('link') and '[Brakeman description]' or None
            )
            self.add_issue(msg)

if __name__ == '__main__':
    import sys
    opts = get_opts('brakeman_import.py', sys.argv)
    print BrakemanCollector(**opts).run(sys.argv[-1])
