import{d as ee,c as z,B as w,s as c,p as f,C as te,f as N,D as ae,i as I,x as R,e as p,g as F,j as a,k as l,t as b,b as _,m as S,E as k,n as G,F as se,G as ie,H as ne,q as re,I as oe,w as T,y as le,z as L,A as de,r as D,a as ce,v as H}from"./SurveyConfigurator.Dgvy2nbL.js";function ue(u,s,t){a(s)>0&&(l(s,a(s)-1),t())}function pe(u,s,t,o,n){s()&&a(t)<o().sections.length-1&&(l(t,a(t)+1),n())}var he=b('<div class="alert alert-danger mb-3">Values are incorrect or missing. Please check the values above before continuing.</div>'),ve=b('<button class="btn btn-primary">Next &gt;</button>'),me=b('<form method="post"><input type="hidden" name="csrfmiddlewaretoken"> <input type="hidden" name="value"> <button type="submit" class="btn btn-primary">Submit <i class="bx bxs-send"></i></button></form>'),ge=b('<!> <!> <div class="d-flex"><button class="btn btn-primary me-3">&lt; Previous</button> <!></div>',1);function J(u,s){G(s,!0);let t=w(s,"config",15),o=w(s,"value",15),n=w(s,"initValue",7,null),d=w(s,"csrf",7,""),y=c(void 0),h=c(void 0);function Q(e){l(y,f(e)),l(h,!e)}function V(){l(y,!1),l(h,!1)}let E=c(void 0),K=le(()=>JSON.stringify(o())),x=c(f(n()!==null?n():[]));te(()=>{o(a(x))});let v=c(0);function q(){const e=a(E).validate();return Q(e),e}function M(e){q()||e.preventDefault()}var C=ge(),O=N(C);ae(O,17,()=>t().sections,ie,(e,i,r)=>{var m=se(),Z=N(m);{var $=P=>{re(oe(P,{editable:!1,displaySectionType:!1,get config(){return t().sections[r]},set config(g){t(t().sections[r]=g,!0)},get value(){return a(x)[r]},set value(g){a(x)[r]=g}}),g=>l(E,f(g)),()=>a(E))};I(Z,P=>{a(v)===r&&P($)})}p(e,m)});var j=_(O,2);{var U=e=>{var i=he();p(e,i)};I(j,e=>{a(h)&&e(U)})}var B=_(j,2),A=S(B);A.__click=[ue,v,V];var W=_(A,2);{var X=e=>{var i=ve();i.__click=[pe,q,v,t,V],p(e,i)},Y=e=>{var i=me(),r=S(i);L(r);var m=_(r,2);L(m),de(2),D(i),R(()=>{T(r,d()),T(m,a(K))}),ne("submit",i,M),p(e,i)};I(W,e=>{a(v)<t().sections.length-1?e(X):e(Y,!1)})}return D(B),R(()=>A.disabled=a(v)<1),p(u,C),F({get config(){return t()},set config(e){t(e),k()},get value(){return o()},set value(e){o(e),k()},get initValue(){return n()},set initValue(e=null){n(e),k()},get csrf(){return d()},set csrf(e=""){d(e),k()}})}ee(["click"]);z(J,{config:{},value:{},initValue:{},csrf:{}},[],[],!0);const fe=[{title:"A. Releasing Potential",type:"sort",description:"This includes spotting talent, enthusiasm, and resilience, ‘learning by doing’, training and research skill use in practice. It also covers understanding the importance of an enabling environment, facilitating and supporting research careers from the start.",fields:[{type:"likert",name:"releasing_potential",label:"Our organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3= Substantial Progress; 4=Established)",required:!0,sublabels:["A1. has a system to talent spot and support individuals who are active in-service development/ QI to progress on to research","A2. has research role models and named nursing research leaders","A3. identifies and celebrates success in the nursing research related activity","A4. provides research advice sessions where nurses can explore ideas for project development","A5. provides help to nurses to navigate research funding submissions, ethics and governance systems","A6.  has a finance department that can cost research project involvement for external funding applications","A7. has an active research-related mentorship programme","A8. provides mentorship to nurses to successfully apply for internships and fellowship opportunities","A9. enables the use of awarded grant funding in the manner intended (for example, protected time and spending decisions)","A10. provides nurses with access to research learning opportunities to develop research skills delivered through our R&D department, service development, education, or training departments","A11. provides nurses with access to experts who can advise on developing project proposals","A12. has a mission statement that includes an ambition to do research as a core activity","A13. has a strategic document to support research capacity development for nursing","A14. has a research capacity delivery plan which aims to maximise the use, delivery, collaboration and leadership in nursing research","A15. has a dedicated database of projects that are nurse led or where nurses have contributed","A16. monitors research supervision and successful project development and delivery","A17. develops good news stories of research in our internal and external communications","A18. includes research in our induction process","A19. offers pre-registration research placement opportunities","A20. offers continuing professional development in research","A21. provides opportunities to use research skills and experience of leadership at post-masters","A22. provides opportunities to use research skills and experience of leadership at post-doctoral levels."],options:["0","1","2","3","4"],description:""},{type:"textarea",name:"releasing_potential_comments",label:"A23. If you would like to add any comments with regards to any of the statements in section above (Releasing Potential), please write below.",required:!1,sublabels:[],options:[]}]},{title:"Embedding Research",type:"sort",description:"This includes reducing barriers to research related activities by providing time and resources. It covers making research legitimate in the organisation, recognising the impact of research and midwives' contribution to research.",fields:[{type:"likert",name:"embedding_research",label:"Our Organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3= Substantial Progress; 4=Established)",required:!0,sublabels:["B1.  provides protected time for clinical nurses to support research related activities","B2. provides resources (for example, time and/or funds) to support Public and Patient Involvement and Engagement to identify and develop research","B3. develops impact stories from projects where nurses support, participate or lead research","B4. collects case studies of where Public and Patient Involvement and Engagement has made a difference to research","B5. actively communicates to the nursing workforce, clinical managers and executive team about how the involvement of nurses in research has made a difference to services and people"],options:["0","1","2","3","4"]},{type:"textarea",name:"embedding_research_comments",label:"B6. If you would like to add any comments with regards to any of the statements in the section above (Embedding Research), please write below.",required:!1,sublabels:[],options:[]}]},{title:"C. Linkages and Leadership",type:"sort",description:"This includes activities related to forming research links outside the organisation, promoting midwifery research leadership to influence the wider research agenda.",fields:[{type:"likert",name:"linkages_and_leadership",label:"Our organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3= Substantial Progress; 4=Established)",required:!0,sublabels:["C1. take part in research leadership and advisory activities outside our organisation (for example, sitting on ethics committees; funding committees; editorial boards and reviewing papers)","C2. take part in research leadership and advisory activities outside organisations","C3. work with professional bodies and national and regional policy structures to influence the research agenda","C4. are members of forums outside our organisation which support research activity"],options:["0","1","2","3","4"]},{type:"textarea",name:"linkages_and_leadership_comments",label:"C5. If you would like to add any comments with regards to any of the statements in the section above (Linkages and Leadership), please write below.",required:!1,sublabels:[],options:[]}]},{title:"D. Inclusive research delivery",description:"This includes activities related supporting the public and patient’s involvement in research. It also covers engaging the wider nursing workforce in delivering portfolio research, creating more opportunities to deliver research and making the contribution of midwives visible.",type:"sort",fields:[{type:"likert",name:"inclusive_research_delivery",label:"Our organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3= Substantial Progress; 4=Established)",required:!0,sublabels:["D1. have skills to support Public and Patient Involvement and Engagement","D2. use their expertise to deliver research, including portfolio (commercial and non-commercial) research","D3. who deliver research have their contribution recognised in research outputs (for example, through acknowledgement, co-authorship)","D4. who work at an advanced, specialist, and consultant levels of practice act as principal investigators (PIs) for portfolio research"],options:["0","1","2","3","4"]},{type:"textarea",name:"inclusive_research_delivery_comments",label:"D5. If you would like to add any comments with regards to any of the statements in the section above (Inclusive research delivery), please write below.",required:!1,sublabels:[],options:[]}]},{title:"E. Digital enabled research",description:"It covers activities related to research leadership and skills in digital technologies and data science including the skills needed to undertake research and service developments.",type:"sort",fields:[{type:"likert",name:"digital_enabled_research",label:"Our Organisation: (0=Not yet planned; 1=Planned; 2=Early progress; 3= Substantial Progress; 4=Established",required:!0,sublabels:["E1. provides training for nurses to enable them to practise effectively in a digitally enabled environment","E2. trains nurses to use and interpret data to make improvements to care (using audit, service evaluation or research)","E3.  has digital nurse leaders in place who can provide advice and guidance in the use of digital technology in service development","E4. has digital nurse leaders in place who can provide advice and guidance in the use of digital technology in research","E5. has the infrastructure to support visualisation of data using business intelligence tools","E6. has the internal structures that facilitate, support and enable nurse-led digital innovation","E7. has effective partnerships with technology suppliers to support digital developments and innovation that meet the needs of nurses","E8. collects and shares case study examples of improvements to care using digital technology","E9. collects and shares case study examples of improvements to research using digital technology"],options:["0","1","2","3","4"]},{type:"textarea",name:"digital_enabled_research_comments",label:"E10. If you would like to add any comments with regards to any of the statements in the section above (Digital enabled research), please write below.",required:!1,sublabels:[],options:[]}]}],be={sections:fe};var ye=b("<div><!></div>");const we={hash:"svelte-3kpd",code:""};function _e(u,s){G(s,!0),ce(u,we);let t=H("csrf",""),o=c(f(H("configData",be))),n=c(void 0);var d=ye(),y=S(d);J(y,{get config(){return a(o)},csrf:t,get value(){return a(n)},set value(h){l(n,f(h))}}),D(d),p(u,d),F()}customElements.define("survey-configurator",z(_e,{},[],[],!0));export{J as S,_e as a};
