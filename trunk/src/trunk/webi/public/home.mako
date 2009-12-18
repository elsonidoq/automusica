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
<body style="margin:0 auto; " onload="javascript:resize();">
    <div id="jplayer"></div>
    
    <div  > 
        <div id="title-container" >
            <div id="title">La compositora</div>
            <div id="copete">Análisis musical y composición automática</div>
            <div id="space-between-title-and-rest"></div>
        </div>
        <div id="description-container" >
            <div id="description">${description}</div>
        </div>
        <div id="player-container" >
            <div id="player-description"> 
                ${player_description}
                <div id="space-after-player-description"></div>
                 
                <div id="playlist">
                    <%def name="print_song(song_desc, color1, color2)">
                        <% 
                           element_class=song_desc['name'].replace(' ', '_').replace('(','').replace(')','').replace('!','').replace(',','') 
                           link_color="755"
                        %>
                        <div class="song" >
                            <div style="background:#${color1}"> 
                                <a style="color:#${link_color};padding-left:10px;text-decoration:none;background:#${color1}" href="#" 
                                        onclick="javascript:show_songs('#${element_class}');">${song_desc['name']}</a>
                            </div>

                            <div class="song_compositions" id="${element_class}_compositions" >

                                <div class="song_link_div" id="${element_class}_orig" style="background:#${color2}"> 
                                    <img class="play_img" id="${element_class}_orig_play" 
                                        src="/images/play_chico.png" 
                                        style="background:#${color2}"
                                        onclick="javascript:play_sound('${song_desc['orig']}', '#${element_class}_orig');"/> 
                                    
                                    <img class="stop_img" id="${element_class}_orig_stop" 
                                        src="/images/stop_chico.png" 
                                        style="background:#${color2}"
                                        onclick="javascript:stop_song('#${element_class}_orig');"/> 
                                    
                                    <span style="vertical-align:top;color:#${link_color};background:#${color2};text-decoration:none;" href="#"> 
                                        original
                                    </span> 
                                    
                                    <img class="gif_loader" style="background:#${color2};" id="${element_class}_orig_loader" src="/images/loader.gif" /> 
                                </div>

                                <div class="song_link_div" id="${element_class}_solo" style="background:#${color1}"> 

                                    <img class="play_img" id="${element_class}_solo_play" 
                                        src="/images/play_chico.png" 
                                        style="background:#${color1}"
                                        onclick="javascript:play_sound('${song_desc['solo']}', '#${element_class}_solo');"/> 

                                    <img class="stop_img" id="${element_class}_solo_stop" 
                                        src="/images/stop_chico.png" 
                                        style="background:#${color1}"
                                        onclick="javascript:stop_song('#${element_class}_solo');"/> 
                                    
                                    <span style="vertical-align:top;color:#${link_color};background:#${color1};text-decoration:none;" href="#"> 
                                        con solo
                                    </span> 
                                    <img class="gif_loader" style="background:#${color1};" id="${element_class}_solo_loader" src="/images/loader.gif" /> 

                                </div>
                            </div>
                        </div>
                    </%def>
                                
                    <% i=1 %>
                    % for song_desc in songs:
                        <%
                           colors= ["dce0ee", "cbd1f0"]
                           color1 = colors[i]
                           color2 = colors[(i+1)%2]
                           print_song(song_desc, color1, color2)
                           i=(i+1)%2
                        %>
                    % endfor
                </div>
            </div>

        <div style="width:100%;height:80px"></div>

        </div>
        
    
    </div>
        <div style="text-align:center;">
<!--            <div>
                <a style="text-decoration:none;color:#666">
                    <img href="experiment?id=percentiles" style="border:none;" src="/images/right.png"/>
                </a>
             </div> -->
             <a href="experiment?id=percentiles" style="font-size:25px;color:#447;">
                Quiero hacer un experimento
             </a>
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
            jplayer= $("#jplayer");
            jplayer.stop();
        }

        var play_sound= function(name, element_name) {
            if (playing_element != null) {
                stop_song(playing_element);
            }
            playing_element= element_name;
            $(element_name + "_stop").show();
            $(element_name + "_play").hide();
            $(element_name + "_loader").fadeIn();

            base_url= "${songs_base_url}";
            url= base_url + name
            jplayer= $("#jplayer");
            jplayer.setFile(url);
            jplayer.play();
        }
        var resize = function() {
            var player_height= $("#player-container").height()
            var desc_height= $("#description-container").height()

            var new_height= 80;
            if (player_height > desc_height) {
                new_height+= player_height;
            } else {
                new_height+= desc_height;
            }

    /*        $("#player-container").css('height', new_height);
            $("#description-container").css('height', new_height);*/

            $("#playlist").css('padding-left', parseInt($("#player-description").width() - $("#playlist").width())/2);


        }
        
        $(window).resize(resize);
    </script>
</body>
</html>
