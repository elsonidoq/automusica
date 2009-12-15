## -*- coding: utf-8 -*-
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <title> Experimentando con la percepci&oacute;n musical </title>
	<script type="text/javascript" src="/js/jquery.js"></script>
    <script type="text/javascript" src="/js/jquery.jplayer.js"></script>
    
	<link rel="stylesheet" type="text/css" href="/css/home.css"/>
    <script type="text/javascript">
    $(document).ready(function(){
       var jplayer= $("#jplayer").jPlayer({
            ready: function () {



            }
            ,swfPath:'/js/'
        })
        .onProgressChange( function(lp,ppr,ppa,pt,tt) {
/*            if (player.is_muted && lp < 100) {

            } else if(player.is_muted && lp >= 100) {

            } */
                
        }).onSoundComplete( function() {
            player.onSoundComplete();
            
        });



    });

    </script>
</head>
<body style="margin:0 auto; " onload="javascript:resize();">
    <div id="jplayer"></div>
    
    <div id="desc-container" > 
        <div id="title-container" >
            <span id="title">La compositora</span>
        </div>
        <div id="description-container" >
            <div id="description">${description}</div>
        </div>
        <div id="player-container" >
            <div id="player-description"> 
                ${player_description}
            </div>
            
            <div id="playlist">
                <%def name="print_song(song_desc)">
                    <% element_class=song_desc['name'].replace(' ', '_') %>
                    <div class="song" >
                        <div > <a href="#" onclick="javascript:show_songs('.${element_class}');">${song_desc['name']}</a></div>
                        <div class="${element_class}" style="display:none; padding-left:10px"> 
                            <a href="#" onclick="javascript:play_sound('${song_desc['orig']}');"> original</a> 
                        </div>
                        <div class="${element_class}" style="display:none; padding-left:10px"> 
                            <a href="#" onclick="javascript:play_sound('${song_desc['solo']}');"> con solo</a> 
                        </div>
                    </div>
                </%def>
                            
                % for song_desc in songs:
                    ${print_song(song_desc)}
                % endfor
            </div>


        </div>
        
    
    </div>
    <div style=" height:100px"> 
        <div style="text-align:center">
            <a href="experiment">Quiero hacer un experimento</a>
        </div>
    
    </div>


    <script type="text/javascript">
        
        var show_songs = function(element_class) {
            $(element_class).slideToggle();

        }
        var play_sound= function(name) {
            base_url= "${songs_base_url}";
            url= base_url + name
            jplayer= $("#jplayer");
            jplayer.setFile(url);
            jplayer.play();
        }
        var resize = function() {
            var h= $(window).height();
            var title_container_height= $("title-container").height();
            $("#desc-container").css('height', h*3/4);
            $("#player-container").css('height', h*3/4-title_container_height);
            $("#description-container").css('height', h*3/4-title_container_height);


        }
        
        $(window).resize(resize);
    </script>
</body>
</html>
