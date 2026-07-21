function isMobile() {
	let agent = navigator.userAgent.toUpperCase();
	let result = false;
	
	if(agent.indexOf("IPHONE") > -1 || agent.indexOf("ANDROID") > -1){
		result = true;
	}
	
	return result;
}

function clip(lang){
	
	var url = '';
	var textarea = document.createElement("textarea");
	
	document.body.appendChild(textarea);
	url = window.document.location.href;
	
	textarea.value = url;
	textarea.select();
	document.execCommand("copy");
	document.body.removeChild(textarea);
	
	if(lang == "ENG"){
		alert("The URL has been copied.");
	}
	else{
		alert("URL이 복사되었습니다.");
	}
	
}

function pageFunctionReport(pg, thisObj){
	authorReportList(pg, thisObj);
}

function pageFunctionEtc(pg, thisObj){
	authorEtcList(pg, thisObj);
}

function listEmpty() {
	$("#reportArea").empty();
	$("#etcArea").empty();
}

function authorSlider(thisObj) {
		
	var url = $(thisObj).attr("data-ajax-url");
	var aut_no = $(thisObj).attr("data-no");
	var target = $("#authorArea");
	var markup = "";
	
	var reportPg
	
	$.ajax({
		
		  url      : url
		, type     : 'POST'
		, data     : { "aut_no" : aut_no }
		, dataType : 'json'
		, success : function ( data ) {
			
			if ( data.status ) {
				
				target.empty();
				
				// 저자번호 담은 input 추가
				markup += '<input type="hidden" id="author" value="' + aut_no + '"/>' ;
				
				markup += data.markup;
				
				target.append(markup);
				
				kdifn.slideLeftOpen('.move_research-team');
				
				authorReportList('1', $("#reportBtn")); // 보고서 리스트 호출
				authorEtcList('1', $("#etcBtn")); // 기타 리스트 호출
				
			} else {
				alert(data.msg);
			}
			
		} , error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
        	return false;
		}
		
	});
	
}

function authorReportList(pg, thisObj) {
	
	var url = $(thisObj).attr("data-ajax-url");
	var aut_no = $("#author").val();
	var target = $("#reportArea");
	var markup = "";
	
	$.ajax({
		
		  url : url
		, type : 'POST'
		, data : { "aut_no" : aut_no, "pg" : pg }
		, dataType : 'json'
		, success : function ( data ) {
			
			target.empty();
			
			if ( data.list.length > 0 ) {
				
				markup += '<ul>';
			
				$(data.list).each(function(i){
					
					markup += '<li>';
					markup +=	'<em>' + data.list[i].CD_NM_KORN + '</em>';
					markup +=	'<p>';
					markup +=		'<a href="' + data.list[i].PATH + '">' + data.list[i].PUB_NM_KORN + '</a>';
					
					if ( data.list[i].AUT_YN == 'Y' ) 
						markup += '<span><b>' + data.list[i].AUT_NM_KORN + ' 외</b><em>' + data.list[i].ISSU_DT + '</em></span>';
					else 
						markup += '<span><b>' + data.list[i].AUT_NM_KORN + '</b><em>' + data.list[i].ISSU_DT + '</em></span>';
					
					markup +=	'</p>'
						
					if ( data.list[i].pdf_atch_all != '' ) {
						markup +=	'<button type="button" onclick="javascript:location.href=\'/common/file/download?atch_no=' + data.list[i].pdf_atch_all + '\'">다운로드</button>'
					}
					
					markup += '</li>';
					
				});
				
				markup += '</ul>';
				markup += '<div class="comm_pagination">';
				markup +=	data.paging;
				markup += '</div>';
				
			} else {
				
				markup += '<p class="no_search-wrap">※ 결과가 없습니다</p>';
				
			}
			
			target.append(markup);
			
		} , error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
        	return false;
		}
		
	});
	
}



function authorEtcList(pg, thisObj) {
	
	var url = $(thisObj).attr("data-ajax-url");
	var aut_no = $("#author").val();
	var target = $("#etcArea");
	var markup = "";
	
	$.ajax({
		
		  url : url
		, type : 'POST'
		, data : { "aut_no" : aut_no, "pg" : pg }
		, dataType : 'json'
		, success : function ( data ) {
			
			target.empty();
			
			if ( data.list.length > 0 ) {
				
				markup += '<ul>';
			
				$(data.list).each(function(i){
					
					markup += '<li>';
					markup +=	'<em>' + data.list[i].CATEGORY + '</em>';
					markup +=	'<p>';
					markup +=		'<a href="' + data.list[i].PATH + '">' + data.list[i].NM + '</a>';
					
					if ( data.list[i].AUT_YN == 'Y' ) 
						markup += '<span><b>' + data.list[i].AUT_NM + ' 외</b><em>' + data.list[i].DT + '</em></span>';
					else 
						markup += '<span><b>' + data.list[i].AUT_NM + '</b><em>' + data.list[i].DT + '</em></span>';
					
					markup +=	'</p>'
					
					if ( data.list[i].TYPE == 'A' ) {
						if ( data.list[i].pdf_atch_all != null ) {
							markup +=	'<div class="rpt_link"><button type="button" name="button" class="i09" onclick="javascript:location.href=\'/common/file/download?atch_no=' + data.list[i].pdf_atch_all + '\'">첨부파일</button></div>';
						}
					} else {
						if ( data.list[i].FILE_CNT > 0 ) {
							if ( data.list[i].FILE_CNT == 1 ) {
								markup += '<div class="rpt_link"><button type="button" name="button" class="i09" onclick="fileDown(\'' + data.list[i].TYPE + '\', \'' + data.list[i].NO +'\');">첨부파일</button></div>';
							} else if ( data.list[i].FILE_CNT > 1 ) {
								markup += '<div class="rpt_link"><button type="button" name="button" class="i09" onclick="arrayFileDown(\'' + data.list[i].TYPE + '\', \'' + data.list[i].NO +'\', this);fileBubble(this, 1);">다운로드</button></div>';
								markup += '<div class="file_bubble">';
								markup += 	'<div class="top">';
								markup += 		'<strong>첨부파일</strong>';
								markup += 		'<span class="txt_fly"><button type="button" name="button" onclick="fileBubble(this, 0);">닫기</button></span>';
								markup += 	'</div>';
								markup += 	'<ul id="' + data.list[i].TYPE + '_' + data.list[i].NO + '">';
								markup += 	'</ul>';
								markup += '</div>';
							}
						}
					}
					
					markup += '</li>';
					
				});
				
				markup += '</ul>';
				markup += '<div class="comm_pagination">';
				markup +=	data.paging;
				markup += '</div>';
				
			} else {
				
				markup += '<p class="no_search-wrap">※ 결과가 없습니다</p>';
				
			}
			
			target.append(markup);
			
		} , error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
        	return false;
		}
		
	});
	
}

function fileDown(etc_type, no) {
	
	var file_url = '';
	var type = '';
	
	if ( etc_type == 'D' ) type = 'D_KORN';
	else if ( etc_type == 'N' ) type = 'N_KORN';
	else if ( etc_type == 'SM' ) type = 'SM';
	else if ( etc_type == 'SD' ) type = 'SD';
	else {
		alert("잘못된 접근입니다.");
		return false;
	}
	
	if ( etc_type == 'D' || etc_type == 'N' ) file_url = '/board/file/download';
	else if ( etc_type == 'SM' || etc_type == 'SD' ) file_url = '/seminar/file/download';
	
	$.ajax({
		
		  url : '/research/authorEtcAtch'
		, type : 'POST'
		, data : { "type" : type, "no" : no }
		, dataType : 'json'
		, success : function ( data ) {
			
			if ( data.result ) {
				location.href = file_url + "?atch_no=" + data.atch_no;
			} else {
				alert("처리 실패하였습니다.");
				return false;
			}
			
		} , error : function( request, status, error ) {
			
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
        	return false;
        	
		}
		
	});
	
}


function arrayFileDown(etc_type, no, thisobj) {
	
	var file_url = '';
	var type = '';
	var markup = '';
	
	if ( etc_type == 'D' ) type = 'D_KORN';
	else if ( etc_type == 'N' ) type = 'N_KORN';
	else if ( etc_type == 'SM' ) type = 'SM';
	else if ( etc_type == 'SD' ) type = 'SD';
	else {
		alert("잘못된 접근입니다.");
		return false;
	}
	
	if ( etc_type == 'D' || etc_type == 'N' ) file_url = '/board/file/download';
	else if ( etc_type == 'SM' || etc_type == 'SD' ) file_url = '/seminar/file/download';
	
	$.ajax({
		
		  url : '/research/authorEtcArrayAtch'
		, type : 'POST'
		, data : { "type" : type, "no" : no }
		, dataType : 'json'
		, success : function ( data ) {
			
			if ( data.result ) {
				
				var target = $("#" + etc_type + "_" + no);
				
				$(data.list).each(function(i){
					markup += '<li><a href="' + file_url + '?atch_no=' + data.list[i].ATCH_NO + '">' + data.list[i].SV_NM + '</a></li>';
				});
				
				target.append(markup);
				
			} else {
				alert("처리 실패하였습니다.");
				return false;
			}
			
		} , error : function( request, status, error ) {
			
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
      	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
      	return false;
      	
		}
		
	});
}

function makeEmpPop(emp_own_no) {
//	kietfn.loadingBarOpen();
		
	if(emp_own_no == "" || emp_own_no === undefined){
		alert("오류가 발생했습니다.");
		location.reload();
		return false;
	}
	
	let param = {"emp_own_no" : emp_own_no
				,"pg" : "1"
				,"pp" : "10"
				,"gubun" : "A"
				};
	
	$.ajax({
		  type     : 'POST'
		, url      : '/report/getReportByAuthor'
		, data     : param
		, dataType : 'json'
		, success  : function(data) {
			kietfn.loadingBarClose();
			
			if(data.result){
				if(data.info01 === undefined){
					return false;
				}
				$("#info01").empty();
				$("#info01").append(data.info01);
				$("#info02").empty();
				$("#info02").append(data.info02);
				
				$("#pf_cont_div").empty();
				$("#pf_cont_div").append(data.html);
				
				$("#pagingAjax").empty();
				if(data.pagingAjax !== undefined) $("#pagingAjax").append(data.pagingAjax);
				$("#hidden_pop_pg").val(data.pg);
				$("#hidden_pop_pp").val(data.pp);
				$("#hidden_pop_emp_own_no").val(data.emp_own_no);
				
				//Count 값 넣기
				$("#hidden_ardCount").val(data.ardCount);
				$("#hidden_thesisCount").val(data.thesisCount);
				$("#hidden_vdoCount").val(data.vdoCount);
				$("#hidden_svcCount").val(data.svcCount);
				$("#hidden_osbtCount").val(data.osbtCount);
				$("#hidden_seminarCount").val(data.seminarCount);
				$("#hidden_medataCount").val(data.medataCount);
				$("#hidden_prfmncCount").val(data.prfmncCount);
				
				$(".email").attr("onclick", "checkEmail('"+data.emp_own_no+"')");
				
				if(data.ardCount == 0) {
					$("#li_mo_01").hide();
					$("#li_pc_01").hide();
				}
				if(data.thesisCount == 0) {
					$("#li_mo_02").hide();
					$("#li_pc_02").hide();
				}
				if(data.vdoCount == 0) {
					$("#li_mo_03").hide();
					$("#li_pc_03").hide();
				}
				if(data.svcCount == 0) {
					$("#li_mo_04").hide();
					$("#li_pc_04").hide();
				}
				if(data.osbtCount == 0) {
					$("#li_mo_05").hide();
					$("#li_pc_05").hide();
				}
				if(data.seminarCount == 0) {
					$("#li_mo_06").hide();
					$("#li_pc_06").hide();
				}
				if(data.medataCount == 0) {
					$("#li_mo_07").hide();
					$("#li_pc_07").hide();
				}
				if(data.prfmncCount == 0) {
					$("#li_mo_08").hide();
					$("#li_pc_08").hide();
				}
				
				let target = $("#li_pc_01").find("button");
				
				//reset
				kietfn.commonTabFn(target, '.pf_tab li', '.pf_box', 0);
				$("#hidden_pop_gubun").val("A");
				
				setTimeout(function(){
					kietfn.sidePopupOpen('#researchInfo');
				}, 500)
			}
			else{
				alert("오류가 발생했습니다");
				location.reload();
				return false;
			}
		}
		, error    : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
			alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
			return false;
		}
	});
}


function pageFunctionAjax(pageNo){
	if(pageNo !== undefined && pageNo != ""){
		$("#hidden_pop_pg").val(pageNo);
	}
	
	let param = {
				 "emp_no" : $("#hidden_pop_emp_own_no").val()
				,"pg" : $("#hidden_pop_pg").val()
				,"pp" : $("#hidden_pop_pp").val()
				};
				
	$.ajax({
		  type     : 'POST'
		, url      : '/report/getReportByAuthor'
		, data     : param
		, dataType : 'json'
		, success  : function(data) {
			if ( data.length != 0 ) {
				$("#list").empty();
				$("#list").append(data.html);
				
				$("#paging").empty();
				$("#paging").append(data.pagingAjax);
				
				$("#hidden_pop_pg").val(data.pg);
				$("#hidden_pop_pp").val(data.pp);
				$("#hidden_pop_emp_own_no").val(data.emp_own_no);
				
				$(".email").attr("onclick", "checkEmail('"+data.emp_own_no+"')");
			}
			else{
				alert("오류가 발생했습니다");
				location.reload();
				return false;
			}
			
		}
		, error    : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
			alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
			return false;
		}
	});
}

function change_pp_ajax(pvalue){
	$("#hidden_pop_pp").val(pvalue);
	pageFunctionAjax();
}

function setGubunAjax(thisObj, gubun){
	if(gubun === undefined || gubun == "") gubun = "A";
	$("#pop_ttl").text($(thisObj).text());
	$("#hidden_pop_gubun").val(gubun);
	$("#hidden_pop_pg").val('1');
	pageFunctionAjax();
}

function change_pp_ajaxEng(pvalue){
	$("#hidden_pop_pp").val(pvalue);
	pageFunctionAjaxEng();
}

function setGubunAjaxEng(thisObj, gubun){
	if(gubun === undefined || gubun == "") gubun = "A";
	$("#pop_ttl").text($(thisObj).text());
	$("#hidden_pop_gubun").val(gubun);
	$("#hidden_pop_pg").val('1');
	pageFunctionAjaxEng();
}

function checkEmail(emp_own_no) {
	if(emp_own_no === undefined || emp_own_no == ""){
		alert("오류가 발생했습니다.");
		location.reload();
		return false;
	}
	$("#hidden_pop_emp_own_no").val(emp_own_no);
	getImageAjax();
	kietfn.sidePopupClose('#researchInfo');
	kietfn.miniPopupOpen('#security');
}



function getImageAjax(){
		var rand = Math.random();
		var url = '/common/getCaptchaImg?rand='+rand; 
		
		$("#captcha_div").empty();
		let html = ""; 
		html += "<img src='"+url+"' alt='보안문자' >";
		html += "<label for='security_txt'><button type='button' onclick='getImageAjax();'>보안문자 다시 보기</button></label>";
		$("#captcha_div").append(html);
}

function checkCaptcha() {
	// 보안문자 확인      
	let captcha_answer = $("#captcha_answer").val();
	let emp_own_no = $("#hidden_pop_emp_own_no").val();
	
	if(captcha_answer == "" || emp_own_no == ""){
		alert("오류가 발생했습니다. 다시 시도해주세요.");
		location.reload();
		return false;		
	}
	
	$.ajax({
		type : 'POST'
		,url : '/common/checkCaptcha'
		,data : {"captcha_answer" : captcha_answer, "emp_own_no" : emp_own_no}
		,success : function(data){
				console.log(data);
				if(!data.result){
					alert('보안문자 입력값이 일치하지 않습니다.');
					$("#captcha_answer").val(""); 
					getImageAjax();
					return false;
				}
				
				//이메일 확인창 open
				$("#email_text").text(data.email);
				kietfn.miniPopupClose('#security');
				kietfn.miniPopupOpen('#managerInfo');
				
			} 
			, error:function(request,status,error){
	        	console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
	        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
	        	return false;
       		}	
		});
}

function showEmail(menu_cd_ss) {
	$("#hidden_menu_cd_ss").val(menu_cd_ss);
	getImageAjaxEmail();
	kietfn.miniPopupOpen('#emailSecurity');
}

function showEmailGubun(menu_gubun) {
	$("#hidden_menu_gubun").val(menu_gubun);
	getImageAjaxEmail();
	kietfn.miniPopupOpen('#emailSecurity');
}

function getImageAjaxEmail(){
		var rand = Math.random();
		var url = '/common/getCaptchaImg?rand='+rand; 
		
		$("#captcha_div_email").empty();
		let html = ""; 
		html += "<img src='"+url+"' alt='보안문자' >";
		html += "<label for='security_txt'><button type='button' onclick='getImageAjaxEmail();'>보안문자 다시 보기</button></label>";
		$("#captcha_div_email").append(html);
}

function checkCaptchaEmail() {
	
	// 보안문자 확인      
	let captcha_answer_email = $("#captcha_answer_email").val();
	let menu_cd_ss =  $("#hidden_menu_cd_ss").val();
	let menu_gubun =  $("#hidden_menu_gubun").val();
	
	if(captcha_answer_email == ""){
		alert("오류가 발생했습니다. 다시 시도해주세요.");
		location.reload();
		return false;		
	}
	
	$.ajax({
		type : 'POST'
		,url : '/common/checkCaptchaEmail'
		,data : { "captcha_answer_email" : captcha_answer_email, "menu_cd_ss" : menu_cd_ss, "menu_gubun" : menu_gubun}
		,success : function(data){
				if(!data.result){
					alert('보안문자 입력값이 일치하지 않습니다.');
					$("#captcha_answer_email").val(""); 
					getImageAjax();
					return false;
				}
				
				if(data.ss_email !== undefined && data.ss_email != ""){
					$("#email_text2").text(data.ss_email);					
				}
				
				if(data.menu_gubun_email !== undefined && data.menu_gubun_email != ""){
					$("#email_text2").text(data.menu_gubun_email);					
				}
				
				kietfn.miniPopupClose('#emailSecurity');
				kietfn.miniPopupOpen('#managerInfoEmail');
				
			} 
			, error:function(request,status,error){
	        	console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
	        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
	        	return false;
       		}	
		});
}



function filePreview(fpath, fname, ftype, svname, fno) {		
	$.ajax({
		 type : 'POST'
		,url : '/comm/AuthCheck'	
		,data : {"type" : "FILE", "fno" : fno, "logType" : "P", lang : "KR"}
		,dataType : "json"
		,success : function(data) {			
			if(data.auth_yn == "N"){
				kcifFn.miniPopupOpen('#accessPopup');	
			}else if ( data.auth_yn == "N1" ) {
				alert("로그인이 필요한 서비스 입니다.");
				location.href = "/webUser/login?rtn=" + window.location.pathname + window.location.search;							
			}else{
				window.open("/flexer/view.jsp?SDir="+fpath+"&SName="+fname+"&ftype="+ftype+"&FileName="+encodeURIComponent(svname),'previewPopup','top=1,left=1,width=800,height=600,marginwidth=0,marginheight=0,border=0,scrollbars=1,resizable=yes');
			}
		},error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
  	    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
  	    return false;
		}
	});
}

function boardFilePreview(fpath, fname, ftype, svname, fno) {		
	window.open("/flexer/view.jsp?SDir="+fpath+"&SName="+fname+"&ftype="+ftype+"&FileName="+encodeURIComponent(svname),'previewPopup','top=1,left=1,width=800,height=600,marginwidth=0,marginheight=0,border=0,scrollbars=1,resizable=yes');
}

function fileEngPreview(fpath, fname, ftype, svname, fno) {		
	$.ajax({
		 type : 'POST'
		,url : '/comm/AuthCheck'	
		,data : {"type" : "FILE", "fno" : fno, "logType" : "P", "lang" : "ENG"}
		,dataType : "json"
		,success : function(data) {
			if(data.auth_yn == "N" || data.auth_yn == "N1"){
				kcifFn.miniPopupOpen('#accessPopup');	
			}else{
				window.open("/flexer/view.jsp?SDir="+fpath+"&SName="+fname+"&ftype="+ftype+"&FileName="+encodeURIComponent(svname),'previewPopup','top=1,left=1,width=800,height=600,marginwidth=0,marginheight=0,border=0,scrollbars=1,resizable=yes');
			}
		},error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
  	    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
  	    return false;
		}
	});
}

function filedownload(fno) {
	location.href="/common/file/userDownload?atch_no="+fno;
}

function reportdownload(fno) {		
	$.ajax({
		 type : 'POST'
		,url : '/comm/AuthCheck'
		,data : {"type" : "FILE", "fno" : fno, "logType" : "D", "lang" : "KR"}
		,dataType : "json"
		,success : function(data) {						
			if(data.auth_yn == "N" ){
				kcifFn.miniPopupOpen('#accessPopup');	
			} else if (data.auth_yn == "N1") {
				alert("로그인이 필요한 서비스 입니다.");
				location.href = "/webUser/login?rtn=" + window.location.pathname + window.location.search;
			}else{			
				location.href="/common/file/reportFileDownload?atch_no="+fno+"&lang=KR";
			}
		},error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
   	    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
   	    return false;
		}
	}); 			
}

function engReportdownload(fno) {		
	$.ajax({
		 type : 'POST'
		,url : '/comm/AuthCheck'
		,data : {"type" : "FILE", "fno" : fno, "logType" : "D", "lang" : "ENG"}
		,dataType : "json"
		,success : function(data) {
//			if(data.auth_yn == "N" ){
//				kcifFn.miniPopupOpen('#accessPopup');	
//			}else if(data.auth_yn == "N1"){
//				alert("로그인이 필요한 서비스 입니다.");
//				location.href = "/webUser/login?rtn=" + window.location.pathname + window.location.search;
//			}else{
				location.href="/common/file/reportFileDownload?atch_no="+fno+"&lang=ENG";
//			}
		},error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
   	    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
   	    return false;
		}
	}); 			
}

let satisfied_count = "";
function setSatisfied(menu_cd){
	let gubun = $("input[name='satisfied_select']:checked").val();
	let content = $("#satisfied_content").val();
	
	if(menu_cd === undefined || menu_cd == ""){
		alert("오류가 발생했습니다. 관리자에게 문의해주세요.");
		return false;
	}
	
	if(gubun === undefined || gubun == ""){
		alert("만족도값을 선택해주세요.");
		return false;
	}
	
	if(content === undefined || content == ""){
		alert("만족도 의견을 입력해주세요.");
		return false;
	}
	
	let param = {
		 "menu_cd" : menu_cd
		,"gubun" : gubun
		,"content" : content
		,"site_gubun" : "KR"
	};
	
	if( satisfied_count == 0 ) {	
		satisfied_count++;
		$.ajax({
			
			  url      : '/common/setSatisfied'
			, type     : 'POST'
			, data     : param
			, dataType : 'json'
			, success : function ( data ) {
				if(data.result){
					alert("만족도 조사가 등록되었습니다. 감사합니다.");
					location.reload();
					return false;
				}
				else{
					alert("오류가 발생했습니다. 관리자에게 문의해주세요.");
					location.reload();
					return false;
				}
				
			} , error : function( request, status, error ) {
				console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
	        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
	        	return false;
			}
			
		});
	}
	else{
			alert("처리중입니다.\n잠시만 기다려주세요.");
			return false;
	}
	
}

let satisfied_eng_count = "";
function setSatisfiedEng(menu_cd){
	let gubun = $("input[name='eng_satisfied_select']:checked").val();
	let content = $("#eng_satisfied_content").val();
	
	if(menu_cd === undefined || menu_cd == ""){
		alert("An error has occurred. Please contact your administrator.");
		return false;
	}
	
	if(gubun === undefined || gubun == ""){
		alert("Please select a satisfaction value.");
		return false;
	}
	
	if(content === undefined || content == ""){
		alert("Please enter your satisfaction opinion.");
		return false;
	}
	
	let param = {
		 "menu_cd" : menu_cd
		,"gubun" : gubun
		,"content" : content
		,"site_gubun" : "ENG"
	};
	
	if( satisfied_eng_count == 0 ) {	
		satisfied_eng_count++;
		$.ajax({
			
			  url      : '/common/setSatisfied'
			, type     : 'POST'
			, data     : param
			, dataType : 'json'
			, success : function ( data ) {
				if(data.result){
					alert("Satisfaction survey registered. Thank you.");
					location.reload();
					return false;
				}
				else{
					alert("An error has occurred. Please contact your administrator.");
					location.reload();
					return false;
				}
				
			} , error : function( request, status, error ) {
				console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
	        	alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
	        	return false;
			}
			
		});
	}
	else{
			alert("처리중입니다.\n잠시만 기다려주세요.");
			return false;
	}
	
}


//TODO 영문
function makeEmpPopEng(emp_own_no) {
	kietfn.loadingBarOpen();
	
	$("#li_mo_01").show();
	$("#li_pc_01").show();
	$("#li_mo_02").show();
	$("#li_pc_02").show();
	$("#li_mo_03").show();
	$("#li_pc_03").show();
	$("#li_mo_04").show();
	$("#li_pc_04").show();
	$("#li_mo_05").show();
	$("#li_pc_05").show();
	$("#li_mo_06").show();
	$("#li_pc_06").show();
	$("#li_mo_07").show();
	$("#li_pc_08").show();
		
	if(emp_own_no == "" || emp_own_no === undefined){
		alert("오류가 발생했습니다.");
		location.reload();
		return false;
	}
	
	
	let param = {"emp_own_no" : emp_own_no
				,"pg" : "1"
				,"pp" : "10"
				,"gubun" : "A"
				};
	
	$.ajax({
		  type     : 'POST'
		, url      : '/common/makeEmpPopEng'
		, data     : param
		, dataType : 'json'
		, success  : function(data) {
			kietfn.loadingBarClose();
			
			if(data.result){
				if(data.info01 === undefined){
					return false;
				}
				$("#info01").empty();
				$("#info01").append(data.info01);
				$("#info02").empty();
				$("#info02").append(data.info02);
				
				$("#pf_cont_div").empty();
				$("#pf_cont_div").append(data.html);
				
				$("#pagingAjax").empty();
				if(data.pagingAjax !== undefined) $("#pagingAjax").append(data.pagingAjax);
				$("#hidden_pop_pg").val(data.pg);
				$("#hidden_pop_pp").val(data.pp);
				$("#hidden_pop_emp_own_no").val(data.emp_own_no);
				
				//Count 값 넣기
				$("#hidden_ardCount").val(data.ardCount);
				$("#hidden_thesisCount").val(data.thesisCount);
				$("#hidden_vdoCount").val(data.vdoCount);
				$("#hidden_svcCount").val(data.svcCount);
				$("#hidden_osbtCount").val(data.osbtCount);
				$("#hidden_seminarCount").val(data.seminarCount);
				$("#hidden_medataCount").val(data.medataCount);
				$("#hidden_prfmncCount").val(data.prfmncCount);
				
				$(".email").attr("onclick", "checkEmail('"+data.emp_own_no+"')");
				
				if(data.ardCount == 0) {
					$("#li_mo_01").hide();
					$("#li_pc_01").hide();
				}
				if(data.thesisCount == 0) {
					$("#li_mo_02").hide();
					$("#li_pc_02").hide();
				}
				if(data.vdoCount == 0) {
					$("#li_mo_03").hide();
					$("#li_pc_03").hide();
				}
				if(data.svcCount == 0) {
					$("#li_mo_04").hide();
					$("#li_pc_04").hide();
				}
				if(data.osbtCount == 0) {
					$("#li_mo_05").hide();
					$("#li_pc_05").hide();
				}
				if(data.seminarCount == 0) {
					$("#li_mo_06").hide();
					$("#li_pc_06").hide();
				}
				if(data.medataCount == 0) {
					$("#li_mo_07").hide();
					$("#li_pc_07").hide();
				}
				if(data.prfmncCount == 0) {
					$("#li_mo_08").hide();
					$("#li_pc_08").hide();
				}
				
				let target = $("#li_pc_01").find("button");
				
				//reset
				kietfn.commonTabFn(target, '.pf_tab li', '.pf_box', 0);
				$("#hidden_pop_gubun").val("A");
				
				setTimeout(function(){
					kietfn.sidePopupOpen('#researchInfo');
				}, 500)
			}
			else{
				alert("오류가 발생했습니다");
				location.reload();
				return false;
			}
		}
		, error    : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
			alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
			return false;
		}
	});
}


function pageFunctionAjaxEng(pageNo){
	if(pageNo !== undefined && pageNo != ""){
		$("#hidden_pop_pg").val(pageNo);
	}
	
	let param = {
				 "emp_own_no" : $("#hidden_pop_emp_own_no").val()
				,"pg" : $("#hidden_pop_pg").val()
				,"pp" : $("#hidden_pop_pp").val()
				,"gubun" : $("#hidden_pop_gubun").val()
				,"ardCount" : $("#hidden_ardCount").val()
				,"thesisCount" : $("#hidden_thesisCount").val()
				,"vdoCount" : $("#hidden_vdoCount").val()
				,"svcCount" : $("#hidden_svcCount").val()
				,"osbtCount" : $("#hidden_osbtCount").val()
				,"seminarCount" : $("#hidden_seminarCount").val()
				,"medataCount" : $("#hidden_medataCount").val()
				,"prfmncCount" : $("#hidden_prfmncCount").val()
				};
				
	$.ajax({
		  type     : 'POST'
		, url      : '/common/makeEmpPopEng'
		, data     : param
		, dataType : 'json'
		, success  : function(data) {
			if(data.result){
				if(data.info01 === undefined){
					return false;
				}
				$("#pf_cont_div").empty();
				$("#pf_cont_div").append(data.html);
				
				$("#pagingAjax").empty();
				if(data.pagingAjax !== undefined) $("#pagingAjax").append(data.pagingAjax);
				$("#hidden_pop_pg").val(data.pg);
				$("#hidden_pop_pp").val(data.pp);
				$("#hidden_pop_emp_own_no").val(data.emp_own_no);
				
				$(".email").attr("onclick", "checkEmail('"+data.emp_own_no+"')");
			}
			else{
				alert("오류가 발생했습니다");
				location.reload();
				return false;
			}
			
		}
		, error    : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
			alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
			return false;
		}
	});
}

function youtube_close(target) {
	embed_layer = $(target).html();
	$(target).html(embed_layer);
}

$(function(){		
	
	$("#sval1").keydown(function(e) {		
    	if (e.which == 13)	searchAll('sval1');
	});	
	
	$("#sval2").keydown(function(e) {		
    	if (e.which == 13)	searchAll('sval2');
	});		
	
	$("#sval3").keydown(function(e) {		
    	if (e.which == 13)	searchAll('sval3');
	});
	
	$("#sval").keydown(function(e) {		
    	if (e.which == 13)	searchAll('sval');
	});			
	
	$("#email").keydown(function(e) {		
    	if (e.which == 13)	moveNewsLetter();
	});			
	
});

// 메인 검색
function searchAll(val){			
	var sval = $("input[name='" + val + "']").val();	
	if(!sval){
		alert("검색어를 입력해주세요.");	
	} else {		
		var rs = setKeyWord(sval);			
		if(rs){
			location.href="/search?sval=" + sval;	
		}else{
			alert("일시적인 오류가 발생 했습니다. 잠시 후 다시 시도해 주세요.");				
		}	
	}		
}	

// 검색어 저장
function setKeyWord(value){	
	var rs = false;
	$.ajax({
		type : 'POST',
		url : "/search/setKeyWord",
		data : { "sval" : value},
		dataType : 'json',
		async : false,
		success : function(data){					
			if(data.status == "succ"){
				rs = true;
			}
		},error : function(request, status, error){
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
    return false;
		}
	});				
	
	return rs;
}

function fnMiniPopOpen() {
	kcifFn.miniPopupOpen("#accessPopup");
}

function fnMoveLogin(){	
	alert("로그인이 필요한 서비스 입니다.");
	var url = window.location.pathname + encodeURIComponent(window.location.search);
	location.href = "/webUser/login?rtn=" + url;
} 

function moveNewsLetter(){
	var regExpEmail = /^[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*@[0-9a-zA-Z]([-_.]?[0-9a-zA-Z])*.[a-zA-Z]{2,3}$/i;			// 이메일형식 정규식
	var email = $("#email").val();
	if(!email){
		alert("이메일을 입력해주세요.");
		return;
	} else {
		if(!regExpEmail.test(email)){
			alert("이메일 형식에 맞지 않습니다 다시 입력해주세요");
			$("input[name='email']").focus();
			return;
		}				
	}	
	var form = $("form[name=newsForm]");
	var userYn = $(form).find("#user_yn").val();	
	if (userYn == "Y") {
		form.attr("method", "get");
		form.attr("action", "/member/pwConfirm");
	} else {
		form.attr("method", "post");
		form.attr("action", "/etc/subscription");
	}
	form.submit();	
}

function moveChart(oThis,gubun){
	var sector = "";
	var conti = "";
	if(gubun == "1"){
		sector = $(oThis).closest(".slick-active").find("input[name='sector']").val();
		conti = $(oThis).closest(".slick-active").find("input[name='conti']").val();
	} else {		
		sector = $(oThis).next().find(".slide_wrap").find(".slick-active").find("input[name='sector']").val();
		conti = $(oThis).next().find(".slide_wrap").find(".slick-active").find("input[name='conti']").val();		
	}
	
	var url = "/chart/";
	//금융지표일 경우
	if( sector == "CUR" || sector == "STK" || sector == "COMM" || sector == "INTR" || sector == "FER" ){
		if(sector == "CUR") url += "exchangeList";
		else if(sector == "STK") url += "stockList";
		else if(sector == "COMM") url += "commList";
		else if(sector == "INTR" || sector == "INTR1" || sector == "INTR2") url += "intrList";
		else if(sector == "FER") url += "frgnExchRsrvList";
		url += "?qsec=" + sector + "&qconti=" + conti;
		location.href= url;
	//경제지표일 경우
	}else {
		location.href= url += "ecnmcIndct?ct=" + sector;		
	}	
}
// 차트 엑셀 다운로드
function excelDownChart(code, sector, startdate, enddate) {	
	$.ajax({
		 type : 'POST'
		,url : '/comm/AuthCheck'
		,data : {"type" : "CHART"}
		,dataType : "json"
		,success : function(data) {			
			if(data.auth_yn != "Y"){
				startdate = "";
				enddate = "";
			}
			location.href = "./excelDown?code=" + code + "&sector=" + sector + "&startdate=" + startdate + "&enddate=" + enddate;
		},error : function( request, status, error ) {
			console.log("code:"+request.status+"\n"+"message:"+request.responseText+"\n"+"error:"+error);
   	    alert("일시적인 오류가 발생했습니다.\n다시 시도해주세요.");
   	    return false;
		}
	}); 		
}

