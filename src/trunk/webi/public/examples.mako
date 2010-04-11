## -*- coding: utf-8 -*-
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <meta http-equiv="Content-type" content="text/html;charset=UTF-8" ></meta>
    <title> Experimentando con la percepci&oacute;n musical </title>
	<script type="text/javascript" src="/js/jquery.js"></script>
    <script type="text/javascript" src="/js/jquery.jplayer.js"></script>
	<link rel="stylesheet" type="text/css" href="/css/examples.css"/>
    <script type="text/javascript">
    $(document).ready(function(){
       var jplayer= $("#jplayer").jPlayer({
            ready: function () {



            }
            ,swfPath:'/js'
        })
        .onProgressChange( function(lp,ppr,ppa,pt,tt) {
            if (ppr>0) {
                $(playing_element + "_loader").fadeOut();
            }
            if (ppr >= 100) {
                $(playing_element + "_play").show();
                $(playing_element + "_stop").hide();
                playing_element=null;
            }
                
        });



    });

    </script>
</head>
<%def name="print_song(list_name, song_desc, colors, last_color_index)">
<% 
   element_class=list_name + song_desc['name']
   import re
   element_class= re.sub('\W|_', '', element_class)
   #element_class= element_class.replace(' ', '_').replace('(','').replace(')','').replace('!','').replace(',','').replace('.', '').replace('-','') 
   link_color="755"
%>
<!-- print_song -->
<div class="song" >
    <div style="background:#${colors[last_color_index]}"> 
	<a style="color:#${link_color};padding-left:10px;text-decoration:none;background:#${colors[last_color_index]};cursor:pointer"
		onclick="javascript:show_songs('#${element_class}');">${song_desc['name']}</a>
    </div>

    <div class="song_compositions" id="${element_class}_compositions" >
	% for name, fname in song_desc['songs']:
	<%
	    song_element_class= element_class + name.replace(' ', '_').replace('-','').replace('.','')
	%>
	<div class="song_link_div" id="${song_element_class}" style="background:#${colors[last_color_index]}"> 
	    <img class="play_img" id="${song_element_class}_play" 
		src="/images/play_chico.png" 
		style="background:#${colors[last_color_index]}"
		onclick="javascript:play_sound('${fname}', '#${song_element_class}');"/> 
	    
	    <img class="stop_img" id="${song_element_class}_stop" 
		src="/images/stop_chico.png" 
		style="background:#${colors[last_color_index]}"
		onclick="javascript:stop_song('#${song_element_class}');"/> 
	    
	    <span style="vertical-align:top;color:#${link_color};background:#${colors[last_color_index]};text-decoration:none;" > 
		${name}
	    </span> 
	    
	    <img class="gif_loader" style="background:#${colors[last_color_index]};" id="${song_element_class}_loader" src="/images/loader.gif" /> 
	</div>
	% endfor

    </div>
</div>
<!-- end print_song -->
</%def>
<body style="margin:0 auto; " onload="javascript:resize();">
    <div id="jplayer"></div>
    
    <div  > 
        <div id="title-container" >
            <div id="title">La compositora</div>
            <div id="copete">An&aacute;lisis musical y composici&oacute;n autom&aacute;tica</div>
            <div id="space-between-title-and-rest"></div>
        </div>
        <div id="player-container" >
            % for list_name, songs in all_examples:
		<div class="section">
		    ${list_name}
		</div>
		<div id="playlist">
			
				    
		<% 
            i=1 
            songs.sort(key=lambda x:x['name'])
        %>
		% for song_desc in songs:
		<%
		    
		    colors= ["dce0ee", "cbd1f0"]
		    color1 = colors[i]
		    color2 = colors[(i+1)%2]
		    print_song(list_name, song_desc, colors, i)
		    i=(i+1)%2
		%>
		% endfor
		</div>

        <div style="height:25px;"></div>
	    % endfor

        
        </div>    
    </div>
    

    <script type="text/javascript">
        
        var playing_element = null;

        var show_songs = function(element_class) {
            $(element_class + '_compositions').slideToggle();
        }

        var stop_song= function(element_name) {
            playing_element= null;
            $(element_name + "_loader").fadeOut();
            $(element_name + "_play").show();
            $(element_name + "_stop").hide();
            var jplayer= $("#jplayer");
            jplayer.stop();
        }

        var play_sound= function(url, element_name) {
            if (playing_element != null) {
                stop_song(playing_element);
            }
            playing_element= element_name;
            $(element_name + "_stop").show();
            $(element_name + "_play").hide();
            $(element_name + "_loader").fadeIn();

            var jplayer= $("#jplayer");
            jplayer.setFile(url);
            jplayer.play();
        }
        var resize = function() {
            var player_height= $("#player-container").height()
            var desc_height= $("#description-container").height()

            var new_height= 80;
            if (player_height > desc_height) {
                new_height+= player_height;
                new_height= player_height;
            } else {
                new_height+= desc_height;
                new_height= desc_height;
            }

            $("#player-container").css('height', new_height + 'px');
            $("#description-container").css('height', new_height + 'px');
            var start_experiment_div= $("#start_experiment");
//            start_experiment_div.css('margin-top', new_height - start_experiment_div.height() - $("#description").height() + "px");

            $("#playlist").css('padding-left', parseInt($("#player-description").width() - $("#playlist").width())/2);

//            console.log($(window).height());
 //           console.log($(window).width());


        }
        
        $(window).resize(resize);
    </script>

<!-- Google Analytics -->
<script type="text/javascript">
var gaJsHost = (("https:" == document.location.protocol) ? "https://ssl." : "http://www.");
document.write(unescape("%3Cscript src='" + gaJsHost + "google-analytics.com/ga.js' type='text/javascript'%3E%3C/script%3E"));
</script>
<script type="text/javascript">
try {
var pageTracker = _gat._getTracker("UA-9984620-3");
pageTracker._trackPageview();
} catch(err) {}</script>

</body>
</html>
