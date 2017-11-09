require 'graphviz'

# Create a new graph
g = GraphViz.new( :G, :type => :digraph )
g[:size] = "8.27x11.7" #A4
#g[:size] = "11.7x16.5" #A3
g.node[:shape] = :plaintext


# From https://www.safaribooksonline.com/library/view/ruby-cookbook/0596523696/ch01s15.html
def wrap(s, width=35)
  s.gsub(/(.{1,#{width}})(\s+|\Z)/, "\\1<br/>")
end

def make_page_label(url, title, comment, content)
  result = '<' + 
           '<TABLE BORDER="0"><TR><TD ALIGN="LEFT">' + url + '</TD></TR><TR><TD>' +
	   '<TABLE BORDER="1" CELLSPACING="4" CELLBORDER="0">' +
	   '<TR><TD><B>' + title + '</B><BR ALIGN="CENTER"/>' +
	   '<I>' + wrap(comment) + '</I>' + 
	   '</TD></TR><TR><TD>' + content +
	   '</TD></TR></TABLE>' + 
	   '</TD></TR></TABLE>' +
           '>'
  return(result)
end

def make_button(text, default=false)
  result = "<TABLE BORDER=\"#{default ? "1" : "0"}\" CELLSPACING=\"0\"><TR>" +
           "<TD BORDER=\"1\" BGCOLOR=\"GRAY80\">" +
           text + "</TD></TR></TABLE>"
  return result
end

def make_text_box(text)
  result = "<TABLE BORDER=\"0\" CELLSPACING=\"0\"><TR>" +
           "<TD BORDER=\"1\" BGCOLOR=\"GRAY90\">" +
           wrap(text) + "</TD></TR></TABLE>"
  return result
end

def make_mock_page(title, content)
  result = "<TABLE BGCOLOR=\"YELLOW\" BORDER=\"1\" CELLSPACING=\"1\" CELLBORDER=\"0\">" +
	   "<TR><TD><B>" + title + "</B><BR ALIGN=\"LEFT\"/></TD></TR>" +
	   "<TR><TD>" + content + "</TD></TR>" +
	   "</TABLE>"
  return result
end

def make_edge_label(label)
  return("<<I>" + wrap(label, 10) + "</I>>")
end

welcome = g.add_nodes("welcome")
welcome[:label] = make_page_label(
  '/slat',
  'Welcome Page', 
  'In a cloud deployment, you would need to log in before getting here.',
  make_mock_page("Welcome to WebSLAT", 
                 "<TABLE BORDER=\"0\">" +
                 "<TR><TD COLSPAN=\"2\">Choose an existing project:</TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Redbook example<BR ALIGN=\"LEFT\"/></U></TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Project #1</U><BR ALIGN=\"LEFT\"/></TD></TR>" +
                 "<TR><TD></TD><TD ALIGN=\"LEFT\"><U>Project #2</U><BR ALIGN=\"LEFT\"/></TD></TR>" +
	         "<TR><TD COLSPAN=\"2\" ALIGN=\"CENTER\">Or</TD><TD></TD></TR>" +
                 "<TR><TD COLSPAN=\"2\">" + make_button("Create a new project", false) +
                 "</TD></TR></TABLE>"))

project_editor = g.add_nodes("project_editor")
project_editor[:label] = make_page_label(
  '/slat/project/id#',
  'Project Editor', 
  'This is the main page for the Redbook Example Project.',
  make_mock_page("Redbook Example", 
                 "<TABLE BORDER=\"0\" CELLSPACING=\"0\" CELLBORDER=\"0\">" +
                 "<TR><TD><B>Title</B></TD><TD>" + make_text_box("Redbook Project") + "</TD></TR>"  +
                 "<TR><TD><B>Description</B></TD><TD ALIGN=\"LEFT\">" + 
                 make_text_box("This project is based on the Redbook reference project") + 
                 "</TD></TR>"  +
                 "<TR><TD></TD><TD>" + make_button("Submit Changes") + "</TD></TR>" +
                 "<TR><TD HEIGHT=\"10\" COLSPAN=\"2\"></TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Seismic Hazard") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Engineering Demands") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Component Library") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Component Groups") + "</TD></TR>" +
                 "<TR><TD></TD><TD>" + make_button("Calculations") + "</TD></TR>" +
                 "</TABLE>"))


g.add_edges( welcome, project_editor )[:label] = make_edge_label("Existing Project")

# Generate output image
puts g.output( :none => String )
g.output( :png => "pages-test.png")
g.output( :pdf => "pages-test.pdf")

