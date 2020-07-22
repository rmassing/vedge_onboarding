#!/bin/env perl
use warnings;

# $Id: eman-am,v 1.51 2018/12/11 12:10:12 jonixon Exp $

#------------
# eman-am - Robbie Allen rallen@cisco.com 
#           Copyright 1999, Cisco Systems, Inc.
#
#      All questions should be posted to 'eman-am-dev@cisco.com'
#
#      The only requirements to run this client is the libwww-perl set
#      of modules (preferrably 5.36) and a standard UNIX or Windows 
#      port of Perl 5.004 or better (although you may get away with
#      having an older version)
#
#      There are 3 different 'modes' to run the CLI in:
#         command line mode - define all arguments on a single line
#         interactive mode  - log on and run multiple commands 
#                             w/o re-logging in
#         batch mode        - specify a file to read which has a list 
#                             of commands to run
#
#      For more information run 'perldoc eman-am'
#
#------------

# Flush output
$|++;

# Change depending on OS type - either 'Win' or 'UNIX'
# If it is uncommented, then I'll try to figure it out using $^O
# (which should work with standard ports of Perl)
# --Note: The only non-cross platform aspect of this CLI
#         is how it hides your password as you type it :-(

# $main::OSTYPE = 'Win';  # for all MS Window derivatives 
# $main::OSTYPE = 'UNIX'; # for all UNIX derivatives
# $main::OSTYPE = 'None'; # for all others

$main::CVSVERSION   = '$Revision: 1.51 $';
$main::CVSVERSION   =~ /: (.*) \$/;
$main::VERSION      = "EMAN AM CLI/$1";
$main::console      = '';
$main::default_server = 'am.cisco.com'; # This will get replaced with value 
                                          # provided with -server=hostname argument
$main::url_for_info = "https://am.cisco.com/EMAN/Documentation/user_guide/address_management/CLI/index.cgi";
$main::cgi_path     = "/cli.pcgi";
$main::url_for_cli  = "https://".$main::default_server.$main::cgi_path; # this will be calculated
                                                                       # again inside the script if 
                                                                       # -server=hostname is provided as argument
# Make sure all required modules are available
requirements_test();

# Run the CLI
cli();

exit;


#------------

sub requirements_test {
my ($type);

    unless (defined $main::OSTYPE) {
        if ($^O eq "MSWin32") {
            $main::OSTYPE = "Win";
        }
        elsif (defined $^O) {
            $main::OSTYPE = "UNIX";
        }
    }

    eval {
        require 5.004;
        # almost the same as 'use LWP::UserAgent';
        require LWP::UserAgent; LWP::UserAgent->import(); 
        # Just want to make sure it is there
        require HTTP::Request;
        # Just want to make sure it is there
        require MIME::Base64;
        # almost the same as 'use Win32::Console'
        require Win32::Console, Win32::Console->import() if $main::OSTYPE eq "Win"; 
    };

    if ($@) { 
        print STDERR "\nERROR\n";
     
        eval { require 5.004; };
        if ($@) {print STDERR "   Your version of Perl is not 5.004 or better\n";}

        eval { require LWP::UserAgent; };
        if ($@) {print STDERR "   Could not find LWP::UserAgent\n";}
    
        eval { require HTTP::Request; };
        if ($@) {print STDERR "   Could not find HTTP::Request\n";}
    
        eval { require MIME::Base64; };
        if ($@) {print STDERR "   Could not find MIME::Base64\n";}

        if ($main::OSTYPE eq "Win") {
            eval { require Win32::Console; };
            if ($@) {print STDERR "   Could not find Win32::Console\n";}
            $type = " (for Windows)";
        }
        else {
            $type = " (for UNIX)";
        }

        print STDERR "\neman-am$type requires the following:\n";
        print STDERR "   Perl 5.004 or better recommended\n";
        print STDERR "   libwww-perl 5.36 or better recommended\n";
        print STDERR "   MIME::Base64\n";

        print STDERR "   Win32::Console\n" if $main::OSTYPE eq "Win";
		
        print STDERR "\nFor more information see:\n"; 
        print STDERR "$main::url_for_info\n\n";

        exit;
    }
}


#------------

sub cli {
my ($ua,$arg,$page,$switch,$value,$username,$password,$filename, $line,$val,$new_value,$count,$line_used);
my (@args,@form,@vals);
my (%args);

    # Store ARGV locally 
    @args = @ARGV;

    # Create a user agent object
    $ua = new LWP::UserAgent;

    $ua->agent("$main::VERSION ($main::OSTYPE)". ' - ' . $ua->agent);

    # Either command line or batch mode if @args exist
    if (@args) { 

        # Parse the command line arguments
        foreach $arg(@args) {
            $new_value = '';
            $switch = '';
            $value = '';
		
    	    # Each argument must be preceded by a '-'
            unless ($arg =~ /^-.+/) {
                print STDERR "ERROR: Badly formatted parameters\n";
                exit;
            }
            if ($arg =~ /=/) { ($switch,$value) = $arg =~ /^(.+?)=(.*)$/; }
            else             {  $switch = $arg; }

            # If spaces are present in the command line, I need to make
            # sure to re-quote them (@ARGV strips quotes out)
            if ($value =~ / /) {
                @vals = split/,/,$value;
                foreach $val(@vals) {
                    if ($val =~ / /) {
                        $val = qq("$val");
                    }
                    $new_value .= "$val,";
                }
                chop $new_value if $new_value =~ /,$/;
                $value = $new_value;
                # Now modify the value in the @args array
                $arg = "$switch=$value";
            }

            $args{$switch} = $value;
        }

        # if there is a argument like -server,use that value to connect to cli
        if (exists $args{'-server'} ) {
           my $server = $args{'-server'} ;
           $server =~ s/^\s+//;
           $server =~ s/\s+$//;
           my $len = length($server);
           if( $len == 0){
                print STDERR "ERROR: need  server name with -server parameter\n";
                exit;
           }
           if($server !~ /\.cisco\.com$/i){
               $main::url_for_cli ="https://".$server.".cisco.com".$main::cgi_path;
           }
           else{
               $main::url_for_cli ="https://".$server.$main::cgi_path;
           }
        }
        # batch mode
        if (exists $args{'-b'} or exists $args{'-batch'}) {
            $filename = $args{'-batch'} || $args{'-b'};
            if (!$filename) {
                print STDERR qq(ERROR: File name required for batch mode\n);
            }
            elsif (!(-e $filename)) {
                print STDERR qq(ERROR: File "$filename" does not exist\n);
            }
            elsif (open(FILE,"$filename")) {
                $username = $args{'-username'} || $args{'-u'};
                $password = $args{'-password'} || $args{'-p'};

                $count = '';
                $line_used = '';
                while (defined ($line = <FILE>)) {
                    chomp $line;
                    # Ignore blank lines
                    next unless $line;
                    # Ignore lines that start with '#' 
                    # (so there can be comments in the batch file)
                    next if $line =~ /^\s*\#/;

                    # If first time through the loop and $username OR
                    # $password have not been defined, look to see if
                    # the first line of the batch file contains -u OR 
                    # -p, else prompt for $username OR $password
                    if (not $count 
                        and (not defined $username or not defined $password)) {

                        if (not defined $username) {
                            $username = ($line =~ /(^|\s)(-u|-username)=(\S+)/)[2];
                            $line_used = 1 if defined $username;
                        }
                        if (not defined $password) {
                            $password = ($line =~ /(^|\s)(-p|-password)=(\S+)/)[2];
                            $line_used = 1 if defined $password;
                        }
                        # Display auth prompt if $username and $password are still not defined
                        while (not defined $username or not defined $password) {
                            ($username,$password) = auth_prompt($username,$password);
                            print STDERR "\n";
                        }
                        next if $line_used;
                    }
                    # encode the arguments and skip if it is password - NW2654
                    $line =~ s/([^a-zA-Z0-9_.-])/uc sprintf("%%%02x",ord($1))/eg if ($line !~ /(-p|-password)=/);
                    push @form,"-ARGS$count=$line"; 
                    
                    $count++;
                    # This enables us to split up the batch file so it doesn't
                    # send too many queries to the web server at once 
                    if ($count == 250) {
                        push @form,"-batch=1";
                        push @form,"-quiet=1" if exists $args{'-q'} or exists $args{'-quiet'};
                        query($ua,$username,$password,@form);
                        $count = '';
                        @form = ();
                    }
                }
                if (@form) {
                   push @form,"-batch=1";
                   push @form,"-quiet=1" if exists $args{'-q'} or exists $args{'-quiet'};
                   query($ua,$username,$password,@form);
                }
            }
            else {
                print STDERR qq(ERROR: Could not open file "$filename" - $!\n);
            }
        }
        # command line mode
        elsif (exists $args{'-h'} or exists $args{'-help'} or exists $args{'-H'} or exists $args{'-Help'} or exists $args{'--h'} or exists $args{'--help'}) {
	    $username = "";
            $password = "";			
            query($ua,$username,$password,@args);
        
        } else {
       
            $username = $args{'-username'} || $args{'-u'};
            $password = $args{'-password'} || $args{'-p'};
		    while (not defined $username or not defined $password) { 
		       	($username,$password) = auth_prompt($username,$password); 
		            print STDERR "\n";
		    }
	        query($ua,$username,$password,@args); 
        }
    }

    # interactive mode
    else {
        ($username,$password) = auth_test($ua);

        # So you can kill a long query and return to the AM prompt
        # or if you typo and want to start over
        # Doesn't work on Win32 though ;-(
        $SIG{'INT'} = sub { print "\nAM> " };

        print "\nAM> ";
        while (defined ($line = <STDIN>)) {
            chomp $line;
            unless ($line) {
                print "AM> "; 
                next;
            }
            exit if $line eq "exit" or $line eq "quit";
 
            # encode the arguments
            $line =~ s/([^a-zA-Z0-9_.-])/uc sprintf("%%%02x",ord($1))/eg;
            query($ua,$username,$password,"-ARGS=$line");
            print "AM> ";
        }
        $SIG{'INT'} = "";
    }
}
    
#------------
# Format all the command line options 
# and send it off to the web server and return
# the response
sub query {
my ($ua,$username,$password,@args) = @_;
my ($arg,$page,$query_string,$req,$res,$pager,$tmp,$more);
my (@pagers);

    # By default 'more' output
    $more = 1;

    # Format the arguments
	my $help = undef;
    # Suppress pager unless interactive mode
        $more = '' if (@ARGV);

    foreach $arg(@args) {
        # Each argument must be preceded by a '-'
        unless ($arg =~ /^-/) {
            $page = "ERROR: Badly formatted parameters\n";
            return($page);
        }
        # If this is a batch file, then shouldn't more output
        $more = '' if $arg =~ /^-b(atch)?=/;

        # Ignore password encoding and passing it in query string NW-2654   
        next if ($arg =~ /^(-p=|-password=)/);   

        # Check and encode if any special character is present in args params other than ARGS param NW-2132
	if(($arg_key,$arg_val) = ($arg =~ /-(.*)=(.*)/) and $1 !~ /ARGS.*/ ) {
	    $arg_val =~ s/([^a-zA-Z0-9_.-])/uc sprintf("%%%02x",ord($1))/eg;
	    $arg =~ s/$arg/-$arg_key=$arg_val/;
	}

        $query_string .= "&$arg" unless $arg =~ /^-server/;
        $query_string .= "=" unless $arg =~ /=/;
        $help = 1 if ($arg =~ /^-[hH]elp$|^--help$|^-[hH]$|^--[hH]$/);
    }


    # Create a request
    if ($help) {
	$main::url_for_cli =~ s/(.*)cli\.pcgi/$1help\.cgi/g;
    }
    $req = new HTTP::Request 'POST' => "$main::url_for_cli"; 
    $req->content_type('application/x-www-form-urlencoded');
    $req->content($query_string);

    # 'GET' style of request (now using POST to support _really_ large
    # batch loads
    # $req = new HTTP::Request GET => "$main::url_for_cli?$query_string";

    # Make sure username and password are valid
	 $req->authorization_basic($username,$password) unless ($help);
         
 
    $tmp  = '';
    @pagers = ();
    if ($main::OSTYPE eq 'Win') {
       $main::ENV{'TEMP'} ||= '';
       $main::ENV{'SYSTEMROOT'} ||= '';
       if (-x "$main::ENV{'SYSTEMROOT'}\\system32\\more.com" || -x "$main::ENV{'SYSTEMROOT'}\\command\\more.com") {
          @pagers = ("$main::ENV{'SYSTEMROOT'}\\system32\\more.com /E <", "$main::ENV{'SYSTEMROOT'}\\command\\more.com <");
          if ($main::ENV{'TEMP'}) {$tmp = "$main::ENV{'TEMP'}\\eman-am.$$." . time;}
       }
    }
    elsif ($main::OSTYPE eq 'UNIX') {
       $tmp    = "/tmp/eman-am.$$." . time;
       @pagers = qw( more less pg view cat );
    }

    # Pass request to the user agent and get a response back

    # Attempt to 'more' output 
    if ($more and -t STDOUT and @pagers and $tmp and open(TMP,">$tmp")) {
       close TMP;
       # The response is printed to file $tmp
       $res = $ua->request($req, $tmp);
       
       foreach $pager(@pagers) {
          if (system("$pager $tmp")) {
             $more = '';
          }
          else {
             $more = 1;
             unlink $tmp if -e $tmp;
             last;
          }
       }
    }
    else {
        $more = '';
    }

    # Was not able to 'more' output
    unless ($more) {
       # If the response has already been printed to a file, print that
       if (-s $tmp and open(TMP,"$tmp")) {
          print while <TMP>;
          close(TMP);
          unlink $tmp;
       }
       else {
          # The anonymous sub prints the response as soon as it is received
          $res = $ua->request($req, sub {my ($data, $response, $protocol) = @_; print $data;});
       }
    }
     
    # Check the outcome of the response
    print STDERR "ERROR:" . $res->message . "\n" unless $res->is_success;

    # return($page);
}


#------------
# Test to see if username and password are correct
# Prompt for a username and password if one wasn't already given
# Used for interactive mode
sub auth_test {
my ($ua,$username,$password) = @_;
my ($not_successful,$req,$res);

    while (1) {
        ($username,$password) = auth_prompt($username,$password);
        next unless defined $username;
    
        # Create a request
        $req = new HTTP::Request GET => "$main::url_for_cli";
    
        $req->authorization_basic($username,$password);
    
        # Pass request to the user agent and get a response back
        $res = $ua->request($req);
    
        # Check the outcome of the response
        if ($res->is_success) { last; }
        else                  { 
            undef $username; undef $password; 
            print STDERR "\nERROR : ",$res->message,"\n"; 
        }
    }
    return($username,$password);
}


#------------
# Prompt for a username and password
sub auth_prompt {
my ($username,$password) = @_;

    unless ($username) {
        print STDERR "Username: ";
        $username = <STDIN>;
        chomp $username;
        return(undef,undef) unless $username;
    }
    unless ($password) {
        # Only platform specific feature of this cli, darn it :-(
        if ($main::OSTYPE eq "Win") {
		    ($password) = win_password_prompt();
	}
	elsif ($main::OSTYPE eq "UNIX") {
	    ($password) = unix_password_prompt();		
        }
	else {
            ($password) = clear_txt_password_prompt();		
	}
    }
    return($username,$password);
}


#------------

# UNIX version of the password prompt
# Using stty because it should be on most
# flavors of UNIX whereas most of the screen 
# manipulation Perl modules are not with the 
# standard dist.
sub unix_password_prompt {
my ($password,$path,$stty);
my (@paths);

   # Hope your stty is in one of these dirs!
   @paths = qw( /bin /usr/bin /usr/local/bin /sbin /local/bin );
   # Default is to use the users path if I couldn't find it
   $stty = "stty";

   foreach $path(@paths) {
       if (-f "$path/stty") {
	       $stty = "$path/stty";
               last;
	   }
   }
   print STDERR "Password: ";
   system("$stty -echo");
   $password = <STDIN>;
   system("$stty echo");

   chomp $password;
   return($password);
}


#------------
# Windows version of the password prompt
# Uses Win32::Console which should be on any standard 
# Windows Perl dist.
# All this just so your password won't be echo'd :-(
sub win_password_prompt {
my ($password,$char,$mode);

    # The console variable can not go out of scope or it will
    # mess up the console
        $main::console ||= new Win32::Console(STD_INPUT_HANDLE());
    $mode = $main::console->Mode();
    $main::console->Mode(ENABLE_PROCESSED_INPUT());

    print STDERR "Password: ";
    while (1) {
         $char = $main::console->InputChar(1);
         if ($char eq "\b" and length($password) > 0) { # backspace
            print STDERR "\b \b";
            chop $password;
         } 
         elsif ($char eq "\r") { # carriage return
            last;
         } 
         elsif ($char ne "\b") {
            $password .= $char;
            print STDERR "*";
         }
    }
    $main::console->Mode($mode);
    return($password);
}


#------------
# Ask for a password and don't try to hide it
sub clear_txt_password_prompt {
my ($password);
  
   print STDERR "Password (plain text echo'd): ";
   $password = <STDIN>;
   chomp $password;
   return($password);
}


#------------

__END__

=head1 NAME

eman-am - Command line interface (CLI) for Address Management

=head1 DESCRIPTION

eman-am provides command line access to some of the more commonly
used functions within Address Management. Please contact 
eman-am-dev@cisco.com to request additional functionality.

There are 3 different 'modes':
  command line mode - define all arguments on a single 
                      line
  interactive mode  - log on and run multiple commands
                      w/o re-logging in
  batch mode        - specify a file to read which has 
                      a list of commands to run

=head1 REQUIREMENTS

The only requirements to run this client is the libwww-perl set
of modules (preferrably 5.36) and a standard UNIX or Windows
port of Perl 5.004 or better (although you may get away with
having an older version)

=head1 HELP

To find out more about this CLI and all the currently available
functions, run:

eman-am -Help

=head1 SEE ALSO

For more information including syntax see:
http://eman.cisco.com/EMAN/Documentation/user_guide/address_management/CLI/index.cgi

=head1 AUTHOR

Robbie Allen rallen@cisco.com

=cut

