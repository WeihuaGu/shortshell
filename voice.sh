#! /bin/sh
urltemp="http://tsn.baidu.com/text2audio?lan=zh&cuid=a1b2c3d4ee&ctp=1&tok=24.2d817d1a3417357c4d5f52ce77d60bd1.2592000.1448626807.282335-7144270&tex=";
url=${urltemp}$1;
echo $url;
mplayer "$url" ;
