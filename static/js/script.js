var radio = '';
var drpdwn = '';

$('document').ready(function () {

/*
(function blink() { 
  $('.blink_me').fadeOut(500).fadeIn(500, blink); 
})();*/

// Wrap every letter in a span
$('.ml9 .letters').each(function(){
  $(this).html($(this).text().replace(/([^\x00-\x80]|\w)/g, "<span class='letter'>$&</span>"));
});

anime.timeline({loop: true})
  .add({
    targets: '.ml9 .letter',
    scale: [0, 1],
    duration: 1500,
    elasticity: 600,
    delay: function(el, i) {
      return 45 * (i+1)
    }
  }).add({
    targets: '.ml9',
    opacity: 0,
    duration: 1000,
    easing: "easeOutExpo",
    delay: 1000
  });
 
 
 init();

});

//Checking and validating the form

function init() {
   
   
   $('#submitBtn').click(function(event){
           event.preventDefault();
        
           RMticket();
           rdovalidation();
           dropdownsvalidation();

        var RM = $('#txtRMticket').val();

      if   (RM != '' && radio == true && drpdwn==true){
		$.ajax({
			url: '/submitDetails',
			data: $('form').serialize(),
			type: 'POST',
			success: function(response){

                window.location = "/dependency_check_output";
			//	console.log(response);
            //    if (response.redirect) {
             //      window.location.href = response.redirect;
              //  }
			},
			error: function(error){
				console.log(error);
			}
		});

      }
            
 });
    

 
}

function RMticket() {
        var $txtRMticket= $('#txtRMticket');
        var value= $('#txtRMticket').val();
        if (value== '') {
            $txtRMticket.parent().find('.haserror').show().html("RM ticket should not be empty");
            $txtRMticket.addClass('controlerror');
            $txtRMticket.parents('.form-element').addClass('label')
        }
        else {
            $($txtRMticket).parent().find('.haserror').hide();
            $($txtRMticket).removeClass('controlerror');
            $($txtRMticket).parents('.form-element').removeClass('label')
        }

 }



function  rdovalidation(){
    
    var $radioChecks=$('[name="prod"]');
    if($radioChecks.is(':checked')=== false){
    var idName=$radioChecks.attr('id');
	$("#"+idName).parents("#radio").find('.haserror').show().html("please select one option");
    $("#"+idName).parents('.form-element').addClass('label')
		  
	}
    else
    {
        $("#radio").find('.haserror').hide();
        $("#radio").parents('.form-element').removeClass('label');
        radio = true;
    }
		  
}

function dropdownsvalidation(){
    
     var $dropDowns =$('select');
     
     for(var i=0;i<$dropDowns.length;i++){
	 var $selectedValue=$dropDowns.eq(i);
     var idName=$selectedValue.attr('id');
     if($selectedValue.val() === "-1"){
     $('#'+ idName).parent().find('.haserror').show().html("You should select one option");
     $('#'+ idName).parents('.form-element').addClass('label')
	 }
     else{
     $('#'+ idName).parent().find('.haserror').hide();
     $('#'+ idName).parents('.form-element').removeClass('label')
     drpdwn = true ;
     
     }
 }
}


