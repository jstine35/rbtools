from rbtools import get_package_version, get_version_string
from rbtools.api.errors import APIError
from rbtools.clients import scan_usable_client
from rbtools.clients.perforce import PerforceClient
from rbtools.clients.plastic import PlasticClient
from rbtools.utils.filesystem import get_config_value, load_config_files
from rbtools.utils.process import die
        self.password_mgr.rb_user = options.http_username
        self.password_mgr.rb_pass = options.http_password
        self._lasturl = ""
        if self._lasturl != args[0]:
            self._retried = False

        self._lasturl = args[0]

            self.retried = 0
            if e.http_status not in (401, 404):
                #
                # However in some versions it wants you to be logged in
                # and returns a 401 from the application after you've
                # done your http basic auth
        return get_config_value(configs, 'REPOSITORY')
def debug(s):
    Prints debugging information if post-review was run with --debug
    if DEBUG or options and options.debug:
        print ">>> %s" % s
def tempt_fate(server, tool, changenum, diff_content=None,
               parent_diff_content=None, submit_as=None, retries=3):
    Attempts to create a review request on a Review Board server and upload
    a diff. On success, the review request path is displayed.
    try:
        if options.rid:
            review_request = server.get_review_request(options.rid)
            review_request = server.new_review_request(changenum, submit_as)
        if options.target_groups:
            server.set_review_request_field(review_request, 'target_groups',
                                            options.target_groups)
        if options.target_people:
            server.set_review_request_field(review_request, 'target_people',
                                            options.target_people)
        if options.summary:
            server.set_review_request_field(review_request, 'summary',
                                            options.summary)
        if options.branch:
            server.set_review_request_field(review_request, 'branch',
                                            options.branch)
        if options.bugs_closed:     # append to existing list
            options.bugs_closed = options.bugs_closed.strip(", ")
            bug_set = set(re.split("[, ]+", options.bugs_closed)) | \
                      set(review_request['bugs_closed'])
            options.bugs_closed = ",".join(bug_set)
            server.set_review_request_field(review_request, 'bugs_closed',
                                            options.bugs_closed)
        if options.description:
            server.set_review_request_field(review_request, 'description',
                                            options.description)
        if options.testing_done:
            server.set_review_request_field(review_request, 'testing_done',
                                            options.testing_done)
    except APIError, e:
        if e.error_code == 103: # Not logged in
            retries = retries - 1
            # We had an odd issue where the server ended up a couple of
            # years in the future. Login succeeds but the cookie date was
            # "odd" so use of the cookie appeared to fail and eventually
            # ended up at max recursion depth :-(. Check for a maximum
            # number of retries.
            if retries >= 0:
                server.login(force=True)
                tempt_fate(server, tool, changenum, diff_content,
                           parent_diff_content, submit_as, retries=retries)
                return
        if options.rid:
            die("Error getting review request %s: %s" % (options.rid, e))
        else:
            die("Error creating review request: %s" % e)
    if not server.info.supports_changesets or not options.change_only:
        try:
            server.upload_diff(review_request, diff_content,
                               parent_diff_content)
        except APIError, e:
            sys.stderr.write('\n')
            sys.stderr.write('Error uploading diff\n')
            sys.stderr.write('\n')
            if e.error_code == 105:
                sys.stderr.write('The generated diff file was empty. This '
                                 'usually means no files were\n')
                sys.stderr.write('modified in this change.\n')
                sys.stderr.write('\n')
                sys.stderr.write('Try running with --output-diff and --debug '
                                 'for more information.\n')
                sys.stderr.write('\n')
            die("Your review request still exists, but the diff is not " +
                "attached.")
    if options.reopen:
        server.reopen(review_request)
    if options.publish:
        server.publish(review_request)
    request_url = 'r/' + str(review_request['id']) + '/'
    review_url = urljoin(server.url, request_url)
    if not review_url.startswith('http'):
        review_url = 'http://%s' % review_url
    print "Review request #%s posted." % (review_request['id'],)
    print
    print review_url
    return review_url
def parse_options(args):
    parser = OptionParser(usage="%prog [-pond] [-r review_id] [changenum]",
                          version="RBTools " + get_version_string())
    parser.add_option('--svn-changelist', dest='svn_changelist', default=None,
                      help='generate the diff for review based on a local SVN '
                           'changelist')
                           "paths outside the view). For git, this specifies"
                           "the origin url of the current repository, "
                           "overriding the origin url supplied by the git client.")
    parser.add_option('--http-username',
                      dest='http_username', default=None, metavar='USERNAME',
                      help='username for HTTP Basic authentication')
    parser.add_option('--http-password',
                      dest='http_password', default=None, metavar='PASSWORD',
                      help='password for HTTP Basic authentication')
    user_config, globals()['configs'] = load_config_files(homepath)
    repository_info, tool = scan_usable_client(options)
    tool.user_config = user_config
    tool.configs = configs
        diff, parent_diff = tool.diff_between_revisions(options.revision_range, args,
                                                        repository_info)
    elif options.svn_changelist:
        diff, parent_diff = tool.diff_changelist(options.svn_changelist)