
\version "2.10.33"

%% Generated by lilypond-book.py
%% Options: [raggedright,indent=0\mm,fragment,quote,notime,relative=1,alt=[image of music]]

#(set! toplevel-score-handler ly:parser-print-score)
#(set! toplevel-music-handler (lambda (p m)
                   (print-score-with-defaults
                p (scorify-music m p))))

#(ly:set-option (quote no-point-and-click))

#(define version-seen? #t)





% ****************************************************************
% Start cut-&-pastable-section 
% ****************************************************************

\paper {
  #(define dump-extents #t)
  
  raggedright = ##t
  indent = 0\mm
  linewidth = 160\mm - 2.0 * 0.4\in
}

\layout {
  
}

\relative c''
{


% ****************************************************************
% ly snippet contents follows:
% ****************************************************************
{
<<
  {c8. c16 r4 c ~ c16 c16 r8 }
>>
}



% ****************************************************************
% end ly snippet
% ****************************************************************
}
