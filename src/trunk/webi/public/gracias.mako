<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
</head>
<body style="margin:0 auto;" onload="javascript:onload();">

<div style="height:100%;text-align:center;">
<span class="gracias" style="font-size:50px;position:absolute;"><h1>&iexcl;&iexcl;Gracias!!<h1> </span>
</div>
<script type="text/javascript">
onload = function() {
    var height= $(window).height();
    var width= $(window).width();
    $('.gracias').css({'top':height/2 - $('.gracias').height()/2 + 'px',
                       'left':width/2 - $('.gracias').width()/2 +'px'} );

}
</script>
</body>
</html>
