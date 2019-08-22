
#### remove empty logs #######
grep -v 'log\":\"\\n\","stream\":\"stdout\",\"time\"' logs > tmp

#### remove useless file system print out ######
grep -v "filesystem.Stat\|filesystem.Writer\|filesystem.Move\|filesystem.URL" tmp > tmp1

### remove useless function print out #######
grep -v "blobUploadDispatcher\|StartBlobUpload\|copyFullPayload\|upload\|blobDispatcher\|secret\|endpoint\|startedat\|authorizing" tmp1 > tmp

### remove redis print out ########
grep -v "redis: connect 192.168.0.220:6379\|cmd=" tmp1 > tmp

#### remove some function ########
grep -v "HEAD\|GET\|POST" tmp > tmp1

### remove some my print out ####
grep -v "serveblob: the gid for this goroutine" tmp1 > tmp
grep -v "Allocated new queue\|response completed" tmp > tmp1
#### remove getcontent and putcontent #####
grep -v "filesystem.GetContent\|filesystem.PutContent" tmp1 > tmp

#grep -v "filesystem.Stat\|HEAD\|info for cmd=" logs > tmp
#grep -v "blobUploadDispatcher\|StartBlobUpload\|upload\|start upload location\|startedat\|authorizing\|POST\|filesystem.Writer\|filesystem.PutContent|copyFullPayload\|filesystem.Move" tmp > data
#grep -v "blobDispatcher\|secret\|endpoint\|cmd=\|filesystem.Stat" data > tmp
#grep -v "redis: connect 192.168.0.220:6379\|filesystem.URL\|GetBlob" tmp > data

#grep -v "filesystem.GetContent" data > tmp
#grep -v "filesystem.PutContent" tmp > data
#grep -v "serveblob: the gid for this goroutine" data > tmp
#grep -v "GET" tmp > data

#Allocated new queue
#file cache miss
#response completed

