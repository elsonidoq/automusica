<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">
<html lang="en">
<head>
    <title> Experimentando con la percepci&oacute;n musical </title>
    
	<link rel="stylesheet" type="text/css" href="/css/questions.css"/>
    
	<script src="/js/jquery.js" type="text/javascript"></script>
    <script src="/js/jquery.metadata.js" type="text/javascript"></script>
    <script src="/js/jquery.validate.js" type="text/javascript"></script>
<script type="text/javascript">

        var d={
                rules: {
                    age: {
                        required: true,
                        number: true, 
                        range: [10,80]
                    },
                    gender: "required",
                    music_study_years: {
                        required: function(element) {
                            return $("#music_study").is(':checked');
                        },
                        number:true,
                        range:[0, 40]
                    }
                },
                ignore: ".ignore"

            };
		$(document).ready(function() {
            	$("#questions").validate(d);

		});
$.metadata.setType("attr", "validate");

</script>
<style type="text/css">
form#questions label.error { display: none;
                             margin-left:40px;}	
</style>

</head>
<body style="margin:0 auto;" onload="javascript:onload();">
    <div style="position:absolute" id="description">
    <span style="font-size:17px">Por &uacute;ltimo voy a necesitar que me respondas unas preguntitas, &#161;&#161;Gracias de nuevo!!<br><br></span>
    </div>
    <form id="questions" style="width:500px;position:absolute" action="answer" method="POST" >
        <input type="hidden" name="visitor_id" id="visitor_id" value="${visitor_id}"/>
        <fieldset >        
        <div style="margin-right:20px;margin-left:20px;margin-top:20px">

            <label>
	    	Edad: &nbsp;<input style="width:100px;" class="required" type="text" name="age" id="age" /> 
            </label>
			<br><label for="age" class="error">Por favor, ingresa tu edad</label>
            <br><br>

			Sexo: &nbsp;<label for="gender_male">
				<input  type="radio" id="gender_male" value="m" name="gender"  />
				Masculino
			</label>

			<label for="gender_female">
				<input  type="radio" id="gender_female" value="f" name="gender"/>
				Femenino
			</label>
			<br><label for="gender" class="error">Seleccion&aacute; tu sexo</label>
            <br><br>

                <input type="checkbox" id="music_study" name="music_study"/>
                &#191;Estudiaste m&uacute;sica?
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span id="music_study_years_label">&#191;Cu&aacute;ntos a&ntilde;os?</span>
                <input style="width:100px;" class="required" type="text" 
                        name="music_study_years" id="music_study_years" /> 

             <br>
             <label for="music_study_years" class="error">
                Por favor, ingres&aacute; hace cu&aacute;nto que estudi&aacute;s m&uacute;sica
             </label>
             <br><br>

             <label>
             &#191;Qu&eacute; te pareci&oacute; el experimento?  &#191;Te sentiste c&oacute;modo? <br>
             &#191;Entendiste la consigna?  Escrib&iacute; lo que te parezca<br>
             <textarea name="observations" id="observations" style="width:100%" rows="5"></textarea>
             </label>
             <br>

            <div style="text-align:right">
                <input type="submit" id="mysubmit" value="Enviar"></input>
            </div>
        </div>
        </fieldset>        
    </form>

<script type="text/javascript">
    onload = function() {
        var height= $(window).height();
        var width= $(window).width();
        $('#questions').css({'top':height/2 - $('#questions').height()/2 + 'px',
                           'left':width/2 - $('#questions').width()/2 +'px'} );
        $('#description').css({'top': parseFloat($('#questions').css('top')) - 20 - $("#description").height() + 'px',
                           'left':width/2 - $('#description').width()/2 +'px'} );

       function check() {
            if($("#music_study").is(':checked')) {
                $("#music_study_years").removeAttr("disabled");
            } else {
                $("#music_study_years").attr("disabled", true);
            }
        }

        $("#music_study").click( function() {
            check();
        });

        check();
    }
</script>
</body>
</html>
