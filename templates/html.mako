<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xml:lang="fr" lang="fr" xmlns="http://www.w3.org/1999/xhtml"> 
<head> 
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/> 
    <title>Supervision: cluster ${cluster} each ${step}</title>
    <style type="text/css">
    body { background: white; color: black; font-family: sans-serif; font-size: 12px; }
    h1 { font-size: 16px; }
    </style>
</head>
<body>
    <h1>Accounting cluster ${cluster} interval ${step}</h1>
    <table border="1">
        <tr>
% if step == "day":
            <th>${step}</th>
            <th>interval</th>
            <th>nb jobs</th>
            <th>cpu consumed</th>
            <th>cpu time available</th>
            <th>nb accounts</th>
            <th>active users</th>
% else:
            <th>${step}</th>
            <th>interval</th>
            <th>nb jobs</th>
            <th>cpu consumed</th>
            <th>cpu time available</th>
            <th>nb accounts</th>
            <th>active users</th>
% endif
        </tr>
% for result in results:
        <tr>
            <td>${result[0]}</td>
            <td>${result[1]}</td>
            <td>${result[2]}</td>
            <td>${result[3]}</td>
            <td>${result[4]}</td>
            <td>${result[5]}</td>
            <td>${result[6]}</td>
        </tr>
% endfor
    </table>
</body>
</html>
