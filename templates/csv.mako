% if step == "day":
day;nb jobs;cpu time consumed;cpu time available;nb accounts;nb active users
% else:
${step};interval;nb jobs;cpu time consumed;cpu time available;nb accounts;nb active users
% endif
% for result in results:
${result[0]};${result[1]};${result[2]};${result[3]};${result[4]};${result[5]};
% endfor
% for interval in sorted(userstats_global):

${interval}:

%     for user,stats in userstats_global[interval].iteritems():
${user};${stats['group']};${stats['jobs']};${stats['time']};
%     endfor

%     for group,stats in groupstats_global[interval].iteritems():
;${group};${stats['jobs']};${stats['time']};
%     endfor
% endfor
