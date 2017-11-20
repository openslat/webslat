require 'graphviz'
# Change module defaults so head and tail labels can be formatted as HTML
GraphViz::Constants::GENCS_ATTRS["taillabel"][:type] = :LblString
GraphViz::Constants::EDGESATTRS["taillabel"] = :LblString
GraphViz::Constants::GENCS_ATTRS["headlabel"][:type] = :LblString
GraphViz::Constants::EDGESATTRS["headlabel"] = :LblString

class PageLayout < GraphViz
  def initialize(xGraphName=:G, hopts={}, &block)
    hopts[:type] = :digraph if not hopts[:type]
    super(xGraphName, hopts)
    self[:size] = "8.27x11.7"
    node[:shape] = :plaintext
    @next_link_colour = 0
    @links = Hash.new()
    block.call(self) if block
  end

  def links()
    return @links
  end

  @@link_colours = [:black, :blue, :red, :aquamarine2, :goldenrod1, :aquamarine4,
                    :goldenrod3, :lightslateblue, :indigo, :lightseagreen]

  def add_decision(name, text)
    node = add_nodes(name)
    node[:label] = "<#{text.wrap(10, :center)}>"
    node[:shape] = :diamond
    node[:penwidth] = 3
    return node
  end

  def add_bubble(name, text, dotted=NIL, fillcolor=:white, color=:black)
    node = add_nodes(name)
    node[:label] = "<<I>#{text.wrap(20, :center)}</I>>"
    node[:shape] = :ellipse
    if dotted then
      node[:style] = "filled,dashed"
    else
      node[:style] = "filled"
    end
    node[:color] = color
    node[:fillcolor] = fillcolor
    node[:penwidth] = 3
    return node
  end

  def add_link(root, long_text, short_text=NIL)
    name = root
    short_text = long_text if not short_text
    if not @links[root] then
      @links[root] = {'color' =>@@link_colours[@next_link_colour],
                      'long_text' => long_text,
                      'short_text' => short_text,
                     }
      @next_link_colour = @next_link_colour + 1
    else
      raise "Duplicate Link"
    end
    return add_bubble(name, long_text, false, :antiquewhite, @links[root]['color'])
  end

  def add_ref(root)
    name = root
    if not @links[root] then
      raise "Undefined link"
    end

    k = 1
    while find_node("#{root}#{k}")
      k = k + 1
    end
    name = "#{root}#{k}"

    return add_bubble(name, 
                      @links[root]['short_text'],
                      true,
                      :antiquewhite,
                      @links[root]['color'])
  end

  def add_page(name, url, title, comment, page)
    node = add_nodes(name)
    node[:label] = "<" +
                   "<TABLE BORDER=\"0\">" +
                   "<TR><TD ALIGN=\"LEFT\">#{url}</TD></TR>" +
                   "<TR><TD><TABLE BORDER=\"1\" CELLSPACING=\"4\" CELLBORDER=\"0\">" +
                   "<TR><TD ALIGN=\"CENTER\"><B>#{title}</B><BR/>" +
                   (comment ? "<I>#{comment.wrap()}</I>" : "") +
                   "</TD></TR>" +
                   "<TR><TD>#{page}</TD></TR>" +
                   "</TABLE>" +

                   "</TD></TR></TABLE>" +
                   ">"
    return node
  end

  def add_action(name, description, width=NIL)
    node = add_nodes(name)
    node[:shape] = :parallelogram
    node[:fillcolor] = :cornflowerblue
    node[:style] = :filled
    if width
      node[:label] = "<<I>#{description.wrap(width)}</I>>"
    else
      node[:label] = "<<I>#{description.wrap()}</I>>"
    end
    return node
  end

  def add_tool(name, description, width=NIL)
    node = add_nodes(name)
    node[:shape] = :folder
    node[:fillcolor] = :paleturquoise
    node[:style] = :filled
    if width
      node[:label] = "<<I>#{description.wrap(width)}</I>>"
    else
      node[:label] = "<<I>#{description.wrap()}</I>>"
    end
    return node
  end

  def add_page_ref(name, title)
    node = add_nodes(name)
    node[:label] = "<" + title.wrap(10) + ">"
    node[:shape] = :box
    node[:fillcolor] = "cyan:darkslategray3"
    node[:style] = :filled
    return(node)
  end
  
  def connect(a, b, label=NIL, style=NIL)
    edge = add_edges(a, b)
    if label then
      case style
      when NIL
        edge[:label] = "<<I><FONT POINT-SIZE=\"10\">#{label.wrap(10)}</FONT></I>>"
      when :BOXED
        edge[:taillabel] = "<<TABLE BORDER=\"1\" CELLBORDER=\"0\"><TR><TD><FONT POINT-SIZE=\"10\">#{label.wrap(10)}</FONT></TD></TR></TABLE>>"
      end
    end
    #puts(edge)
    #puts(edge[:label].class)
    #puts(edge[:taillabel].class)
    return edge
  end

end

class String
  def wrap(width=35, justification=:left)
    self.gsub(/(.{1,#{width}})(\s+|\Z)/, "\\1<BR ALIGN=\"#{justification.upcase()}\"/>")    
  end
end

class Label
  def initialize(text, width=NIL)
    @text = text
    @width = width
  end

  def to_s
    if width then
      @text.wrap()
    else
      @text.wrap(width)
    end
  end
end

class Mock_Page
  def initialize(title,&block)
    @title = title
    @contents = ""
    block.call(self) if block
  end

  def add_line(line)
    @contents = "#{@contents}<TR><TD COLSPAN=\"2\">#{line}</TD></TR>"
  end

  def add_space()
    @contents = "#{@contents}<TR><TD COLSPAN=\"2\"></TD></TR>"
  end
  
  def add_value(title, value)
    @contents = "#{@contents}<TR><TD>#{title}</TD><TD BORDER=\"1\">#{value}</TD></TR>"
  end    

  def add_text_box(title, value)
    @contents = "#{@contents}<TR><TD>#{title}</TD><TD BORDER=\"1\" BGCOLOR=\"GRAY90\">#{value}</TD></TR>"
  end    

  def add_list(values)
    @contents = "#{@contents}<TR><TD></TD><TD>"
    values.each {|v|
      @contents = "#{@contents}#{v}<BR ALIGN=\"LEFT\"/>"
    }
    @contents = "#{@contents}</TD></TR>"
  end

  def add_choices(label, values)
    @contents = "#{@contents}<TR><TD>#{label}</TD><TD>" +
                "<TABLE BORDER=\"0\" CELLBORDER=\"1\" BGCOLOR=\"GRAY90\">"
    values.each {|v|
      @contents = "#{@contents}<TR><TD>#{v}</TD></TR>"
    }
    @contents = "#{@contents}</TABLE></TD></TR>"
  end

  def add_button(button, is_default=false)
    @contents = "#{@contents}<TR><TD></TD><TD BORDER=\"" +
                (is_default ? "2" : "1") +
                "\" BGCOLOR=\"GRAY80\">#{button}</TD></TR>"
  end

  def add_subtable(label, data, can_edit=false)
    @contents = "#{@contents}<TR><TD>#{label}</TD><TD><TABLE BORDER=\"0\""
    @contents = "#{@contents}>"
    data.each {|r|
      @contents = "#{@contents}<TR>"
      r.each_with_index {|c,i|
        @contents = "#{@contents}<TD"
        @contents = "#{@contents}  BORDER=\"1\" BGCOLOR=\"GRAY80\"" if can_edit and i > 0
        @contents = "#{@contents}>#{c}</TD>"
      }
      @contents = "#{@contents}</TR>"
    }
    @contents = "#{@contents}</TABLE></TD></TR>"
  end

  def to_s
    result = "<TABLE BGCOLOR=\"YELLOW\" BORDER=\"1\" CELLSPACING=\"5\" CELLBORDER=\"0\">" +
	     "<TR><TD><B>" + @title + "</B><BR ALIGN=\"LEFT\"/></TD></TR>" +
             @contents +
             "</TABLE>"
    return result
  end
end

class Link 
  def initialize(text)
    @text = text
  end

  def to_s
    return "<I>#{@text}</I>"
  end
end

class Bold
  def initialize(text)
    @text = text
  end
  
  def to_s
    return "<B>#{@text}</B>"
  end
end

# Create a new graph
g = PageLayout.new()
welcome = g.add_page( 
  "welcome",
  "/slat",
  "Welcome Page",
  'In a cloud deployment, you would need to log in before getting here.',
  Mock_Page.new("Welcome to WebSLAT") {|m|
    m.add_line("Choose an existing project:")
    m.add_list([Link.new("Redbook Example"), 
                Link.new("Project #1"),
                Link.new("Project #2")])
    m.add_line("Or")
    m.add_button("Create a new project")
  })

project_editor = g.add_page(
  "project_editor",
  '/slat/project/id#',
  'Project Editor', 
  'This is the main page for the Redbook Example Project.',
  Mock_Page.new("Redbook Example") {|m|
    m.add_text_box("Title", "Redbook Project")
    m.add_text_box("Description", "This project is based on the Redbook reference project")
    m.add_space()
    m.add_button("Submit Changes", true)
    m.add_button("Seismic Hazard")
    m.add_button("Engineering Demands")
    m.add_button("Component Library")
    m.add_button("Component Groups")
    m.add_button("Calculations")
  })


new_project = g.add_page(
  "new_project",
  '/slat/project',
  'New Project', 
  NIL,
  Mock_Page.new("Create a Project") {|m| 
    m.add_text_box("Title", "<I>Enter the project's title</I>")
    m.add_text_box("Description", "<I>Describe the project</I>")
    m.add_space()
    m.add_button("Create")
    m.add_button("Cancel", true)
  })

save = g.add_action("save", "Save the Project To the Database", 20)

hazard_editor = g.add_page_ref("hazard_editor", "Hazard Editor")
edp_editor = g.add_page_ref("edp_editor", "EDP  Editor")
component_library = g.add_page_ref("Component_library", "Component Library")
component_groups = g.add_page_ref("Component_groups", "Component Groups")
calculations = g.add_page_ref("calculations_", "Calculations")

g.connect( welcome, project_editor, "Existing Project")
g.connect( welcome, new_project, "Create a New Project")
g.connect( new_project, welcome, "Cancel")
g.connect( new_project, save, "Create")
g.connect( save, project_editor )
g.connect( project_editor, save, "Submit Changes")
g.connect( project_editor, hazard_editor, "Seismic Hazard")
g.connect( hazard_editor, project_editor, "done")
g.connect( project_editor, edp_editor, "Demand Parameters")
g.connect( edp_editor, project_editor, "done")
g.connect( project_editor, component_library, "Components")
g.connect( component_library, project_editor, "done")
g.connect( project_editor, component_groups, "Component Groups")
g.connect( component_groups, project_editor, "done")
g.connect( project_editor, calculations, "Calculations")
g.connect( calculations, project_editor, "done")

# Generate output image
#puts g.output( :none => String )
g.output( :png => "pages-test.png")
#g.output( :pdf => "pages-test.pdf")


seismic_hazard_pages = PageLayout.new()
seismic_hazard_pages["rankdir"] = :TB

node_seismic_hazard = seismic_hazard_pages.add_link("seismic_hazard", "Seismic Hazard")
link_exit = seismic_hazard_pages.add_link("exit", "Back to Project")
main_graph = PageLayout.new("cluster_main")
main_graph[:rankdir] = :TB
seismic_hazard_pages.add_graph(main_graph)

start_link = main_graph.add_link("start", "Start /slat/project/#/hazard", "Start")
start_ref_1 = main_graph.add_ref("start")
start_ref_2 = main_graph.add_ref("start")
start_ref_3 = main_graph.add_ref("start")

exists = main_graph.add_decision("exists", "Does the hazard exist?")               
type = main_graph.add_decision("type", "What is the hazard type?")

hazard_type = main_graph.add_page(
  "hazard_type",
  "/slat/project/#/hazard/choose",
  "Hazard Type",
  NIL,
  Mock_Page.new("Hazard Type") {|m|
    m.add_choices("Choose the hazard type",
                  ["Non-Linear Hyperbolic",
                   "User-defined Hazard Curve",
                   "NZ Standard"])
    m.add_space()
    m.add_button("Commit", true)
    m.add_button("Cancel")
  })

user_def = main_graph.add_page(
  "user_def",
  "/slat/project/#/hazard/interp",
  "Seismic Hazard: User-defined Hazard Curve",
  "Possibly include a plot, or an option to plot.",
  Mock_Page.new("Seismic hazard") {|m|
    m.add_text_box("Type:", "User-defined Hazard Curve")
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_subtable("Points",
                   [[Bold.new("IM"), Bold.new("Rate")],
                    ["0.01", "0.376775"],
                    ["0.02", "0.155188"],
                    ["0.04", "0.054048"],
                    ["...", "..."]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

nzs = main_graph.add_page(
  "nzs",
  "/slat/project/#/hazard/nzs",
  "Seismic Hazard: NZ Standard Curve",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "NZ Standard Curve")
    m.add_subtable("Parameters:",
                   [[Bold.new("Location"), "Christchurch"],
                    [Bold.new("Soil Class"), "C"],
                    [Bold.new("Period"), "1.5"]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

nlh = main_graph.add_page(
  "nlh",
  "/slat/project/#/hazard/nlh",
  "Seismic Hazard: Non-Linear Hyperbolic",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "Non-Linear Hyperbolic")
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]])
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

user_def_edit = main_graph.add_page(
  "user_def_edit",
  "/slat/project/#/hazard/interp/edit",
  "Hazard Point Editor",
  "There will be extra cells at the end of the list; " +
  "more can be added by commiting the form (for now; " +
  "should be a button to to this)." +
  "For now, points can be deleted by setting them " +
  "to 0,0, but there should be a button for this " +
  "as well.",
  Mock_Page.new("Hazard Point Editor") {|m|
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
    m.add_button("Import")
    m.add_button("Commit")
    m.add_button("Cancel")
  })

user_def_import = main_graph.add_page(
  "user_def_import",
  "/slat/project/#/hazard/interp/import",
  "Hazard Point Import",
  "Import points from a file, for interpolation",
  Mock_Page.new("Hazard Point Import") {|m|
    m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
    m.add_choices("File Format:", ["Original SLAT", "CSV"])
    m.add_text_box("Path:", "<I>path/to/imfunc.csv</I>")
    m.add_space()
    m.add_button("Browse")
    m.add_button("Import")
    m.add_button("Cancel")
  })

nzs_edit = main_graph.add_page(
  "nzs_edit",
  "/slat/project/#/hazard/nzs/edit",
  "Seismic Hazard: NZ Standard Curve",
  "Possibly inlcude a plot, or an option to plot",
  Mock_Page.new("Seisimic Hazard") {|m|
    m.add_text_box("Type:", "NZ Standard Curve")
    m.add_subtable("Parameters:",
                   [[Bold.new("Location"), "Christchurch"],
                    [Bold.new("Soil Class"), "C"],
                    [Bold.new("Period"), "1.5"]], true)
    m.add_space()
    m.add_button("Commit")
    m.add_button("Cancel")
  })

nlh_edit = main_graph.add_page(
  "nlh_edit",
  "/slat/project/#/hazard/nlh",
  "Non-Linear Hyperbolic Editor",
  "Possibly include a plot, or an option to plot",
  Mock_Page.new("Seismic Hazard") {|m|
    m.add_text_box("Type:", "Non-Linear Hyperbolic")
    m.add_subtable("Parameters:",
                   [[Bold.new("V<SUB>asy</SUB>"), 1221],
                    [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                    [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
    m.add_space()
    m.add_button("Edit")
    m.add_button("Change Hazard Type")
    m.add_line(Link.new("Return to Project"))
  })

hazard_type_link = main_graph.add_link('hazard_type_link', "Hazard Type")
hazard_type_ref_1 = main_graph.add_ref('hazard_type_link')
hazard_type_ref_2 = main_graph.add_ref('hazard_type_link')
hazard_type_ref_3 = main_graph.add_ref('hazard_type_link')

main_graph.connect(exists, hazard_type_link, "No")
main_graph.connect(exists, type, "Yes")
main_graph.connect(hazard_type_link, hazard_type)
main_graph.connect(user_def, hazard_type_ref_1, "Change Hazard Type", :BOXED)
main_graph.connect(nzs, hazard_type_ref_2, "Change Hazard Type", :BOXED)
main_graph.connect(nlh, hazard_type_ref_3, "Change Hazard Type", :BOXED)

user_def_viewer_link = main_graph.add_link('user_def_viewer_link', "User-defined Hazard Curve Viewer",  "User-defined Viewer")
user_def_viewer_ref = main_graph.add_ref('user_def_viewer_link')
main_graph.connect(user_def_viewer_link, user_def)

nzs_viewer_link = main_graph.add_link('nzs_viewer_link', "NZ Standard Curve Viewer", "NZS Viewer")
nzs_viewer_ref_1 = main_graph.add_ref("nzs_viewer_link")
main_graph.connect(nzs_viewer_link, nzs)

nlh_viewer_link = main_graph.add_link('nlh_viewer_link', "NLH Viewer")
main_graph.connect(nlh_viewer_link, nlh)

done_link = main_graph.add_link("done", "Done") # 
done_ref_1 = main_graph.add_ref("done")
done_ref_2 = main_graph.add_ref("done")
done_ref_3 = main_graph.add_ref("done")
done_ref_4 = main_graph.add_ref("done")

main_graph.connect(hazard_type, done_ref_1, "Cancel", :BOXED)
main_graph.connect(user_def, done_ref_2, "Return to Project")
main_graph.connect(nzs, done_ref_3, "Return to Project")
main_graph.connect(nlh, done_ref_4, "Return to Project")

nlh_ed_link = main_graph.add_link("nlh_ed_link", "NLH Editor")
nlh_ed_ref = main_graph.add_ref("nlh_ed_link")
main_graph.connect(nlh, nlh_ed_link, "Edit", :BOXED)
main_graph.connect(nlh_ed_link, nlh_edit)
main_graph.connect(hazard_type, nlh_ed_ref)

nzs_ed_link = main_graph.add_link("nzs_ed_link", "NZS Editor")
nzs_ed_ref = main_graph.add_ref("nzs_ed_link")
main_graph.connect(nzs, nzs_ed_link, "Edit", :BOXED)
main_graph.connect(nzs_ed_link, nzs_edit)
main_graph.connect(hazard_type, nzs_ed_ref)

interpolated_editor_link = main_graph.add_link("interpolated_editor", "Interpolated Editor")
interpolated_editor_ref_1 = main_graph.add_ref("interpolated_editor")
interpolated_editor_ref_2 = main_graph.add_ref("interpolated_editor")
main_graph.connect(interpolated_editor_link, user_def_edit)
main_graph.connect(hazard_type, interpolated_editor_ref_1)

main_graph.connect(user_def, interpolated_editor_link, "Edit", :BOXED)

main_graph.connect(user_def_edit, user_def_import, "Import", :BOXED)
main_graph.connect(user_def_edit, start_ref_1, "Cancel", :BOXED)

main_graph.connect(type, user_def_viewer_link, "User-defined Hazard Curve")
main_graph.connect(type, nzs_viewer_link, "NZ Standard Curve")
main_graph.connect(type, nlh_viewer_link, "Non-Linear Hyperbolic")
main_graph.connect(start_link, exists)

import_file = main_graph.add_action("import", "Import File")
main_graph.connect(user_def_import, import_file, "Import", :BOXED)
main_graph.connect(import_file, user_def_import, "Error")

save_1 = main_graph.add_action("save_1", "Save to Database")
save_2 = main_graph.add_action("save_2", "Save to Database")
save_3 = main_graph.add_action("save_3", "Save to Database")

main_graph.connect(import_file, save_1, "Success")
main_graph.connect(user_def_edit, save_1, "Commit", :BOXED)
main_graph.connect(nzs_edit, save_2, "Commit", :BOXED)
main_graph.connect(nlh_edit, save_3, "Commit", :BOXED)
main_graph.connect(save_1, user_def_viewer_ref)

main_graph.connect(import_file, interpolated_editor_ref_2, "Cancel")
browse = main_graph.add_tool("browser", "File Browser")
main_graph.connect(import_file, browse, "Browse", :BOXED)
main_graph.connect(browse, import_file)

main_graph.connect(save_2, nzs_viewer_ref_1)
main_graph.connect(nzs_edit, start_ref_2, "Cancel", :BOXED)
main_graph.connect(nlh_edit, start_ref_3, "Cancel", :BOXED)

seismic_hazard_pages.connect(node_seismic_hazard, main_graph.get_node("start"))
seismic_hazard_pages.connect(main_graph.get_node("done"), link_exit)
seismic_hazard_pages.output( :png => "gmain.png")
seismic_hazard_pages.output( :pdf => "gmain.pdf")
puts(seismic_hazard_pages.output( :none => String))


g.subgraph("cluster_two") {|c|
  c.add_node("Cluster Two")
  start_link = g.add_link("start", "Start /slat/project/#/hazard", "Start")
  start_ref_1 = g.add_ref("start")
  start_ref_2 = g.add_ref("start")
  start_ref_3 = g.add_ref("start")

  exists = g.add_decision("exists", "Does the hazard exist?")               
  type = g.add_decision("type", "What is the hazard type?")

  hazard_type = g.add_page(
    "hazard_type",
    "/slat/project/#/hazard/choose",
    "Hazard Type",
    NIL,
    Mock_Page.new("Hazard Type") {|m|
      m.add_choices("Choose the hazard type",
                    ["Non-Linear Hyperbolic",
                     "User-defined Hazard Curve",
                     "NZ Standard"])
      m.add_space()
      m.add_button("Commit", true)
      m.add_button("Cancel")
    })

  user_def = g.add_page(
    "user_def",
    "/slat/project/#/hazard/interp",
    "Seismic Hazard: User-defined Hazard Curve",
    "Possibly include a plot, or an option to plot.",
    Mock_Page.new("Seismic hazard") {|m|
      m.add_text_box("Type:", "User-defined Hazard Curve")
      m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
      m.add_subtable("Points",
                     [[Bold.new("IM"), Bold.new("Rate")],
                      ["0.01", "0.376775"],
                      ["0.02", "0.155188"],
                      ["0.04", "0.054048"],
                      ["...", "..."]])
      m.add_space()
      m.add_button("Edit")
      m.add_button("Change Hazard Type")
      m.add_line(Link.new("Return to Project"))
    })

  nzs = g.add_page(
    "nzs",
    "/slat/project/#/hazard/nzs",
    "Seismic Hazard: NZ Standard Curve",
    "Possibly include a plot, or an option to plot",
    Mock_Page.new("Seismic Hazard") {|m|
      m.add_text_box("Type:", "NZ Standard Curve")
      m.add_subtable("Parameters:",
                     [[Bold.new("Location"), "Christchurch"],
                      [Bold.new("Soil Class"), "C"],
                      [Bold.new("Period"), "1.5"]])
      m.add_space()
      m.add_button("Edit")
      m.add_button("Change Hazard Type")
      m.add_line(Link.new("Return to Project"))
    })

  nlh = g.add_page(
    "nlh",
    "/slat/project/#/hazard/nlh",
    "Seismic Hazard: Non-Linear Hyperbolic",
    "Possibly include a plot, or an option to plot",
    Mock_Page.new("Seismic Hazard") {|m|
      m.add_text_box("Type:", "Non-Linear Hyperbolic")
      m.add_subtable("Parameters:",
                     [[Bold.new("V<SUB>asy</SUB>"), 1221],
                      [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                      [Bold.new("alpha<SUB>asy</SUB>"), 62.2]])
      m.add_space()
      m.add_button("Edit")
      m.add_button("Change Hazard Type")
      m.add_line(Link.new("Return to Project"))
    })

  user_def_edit = g.add_page(
    "user_def_edit",
    "/slat/project/#/hazard/interp/edit",
    "Hazard Point Editor",
    "There will be extra cells at the end of the list; " +
    "more can be added by commiting the form (for now; " +
    "should be a button to to this)." +
    "For now, points can be deleted by setting them " +
    "to 0,0, but there should be a button for this " +
    "as well.",
    Mock_Page.new("Hazard Point Editor") {|m|
      m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
      m.add_subtable("Parameters:",
                     [[Bold.new("V<SUB>asy</SUB>"), 1221],
                      [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                      [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
      m.add_button("Import")
      m.add_button("Commit")
      m.add_button("Cancel")
    })

  user_def_import = g.add_page(
    "user_def_import",
    "/slat/project/#/hazard/interp/import",
    "Hazard Point Import",
    "Import points from a file, for interpolation",
    Mock_Page.new("Hazard Point Import") {|m|
      m.add_choices("Interpolation Method:", ["Log-log", "Linear"])
      m.add_choices("File Format:", ["Original SLAT", "CSV"])
      m.add_text_box("Path:", "<I>path/to/imfunc.csv</I>")
      m.add_space()
      m.add_button("Browse")
      m.add_button("Import")
      m.add_button("Cancel")
    })

  nzs_edit = g.add_page(
    "nzs_edit",
    "/slat/project/#/hazard/nzs/edit",
    "Seismic Hazard: NZ Standard Curve",
    "Possibly inlcude a plot, or an option to plot",
    Mock_Page.new("Seisimic Hazard") {|m|
      m.add_text_box("Type:", "NZ Standard Curve")
      m.add_subtable("Parameters:",
                     [[Bold.new("Location"), "Christchurch"],
                      [Bold.new("Soil Class"), "C"],
                      [Bold.new("Period"), "1.5"]], true)
      m.add_space()
      m.add_button("Commit")
      m.add_button("Cancel")
    })

  nlh_edit = g.add_page(
    "nlh_edit",
    "/slat/project/#/hazard/nlh",
    "Non-Linear Hyperbolic Editor",
    "Possibly include a plot, or an option to plot",
    Mock_Page.new("Seismic Hazard") {|m|
      m.add_text_box("Type:", "Non-Linear Hyperbolic")
      m.add_subtable("Parameters:",
                     [[Bold.new("V<SUB>asy</SUB>"), 1221],
                      [Bold.new("IM<SUB>asy</SUB>"), 29.8],
                      [Bold.new("alpha<SUB>asy</SUB>"), 62.2]], true)
      m.add_space()
      m.add_button("Edit")
      m.add_button("Change Hazard Type")
      m.add_line(Link.new("Return to Project"))
    })

  hazard_type_link = g.add_link('hazard_type_link', "Hazard Type")
  hazard_type_ref_1 = g.add_ref('hazard_type_link')
  hazard_type_ref_2 = g.add_ref('hazard_type_link')
  hazard_type_ref_3 = g.add_ref('hazard_type_link')

  g.connect(exists, hazard_type_link, "No")
  g.connect(exists, type, "Yes")
  g.connect(hazard_type_link, hazard_type)
  g.connect(user_def, hazard_type_ref_1, "Change Hazard Type", :BOXED)
  g.connect(nzs, hazard_type_ref_2, "Change Hazard Type", :BOXED)
  g.connect(nlh, hazard_type_ref_3, "Change Hazard Type", :BOXED)

  user_def_viewer_link = g.add_link('user_def_viewer_link', "User-defined Hazard Curve Viewer",  "User-defined Viewer")
  user_def_viewer_ref = g.add_ref('user_def_viewer_link')
  g.connect(user_def_viewer_link, user_def)

  nzs_viewer_link = g.add_link('nzs_viewer_link', "NZ Standard Curve Viewer", "NZS Viewer")
  nzs_viewer_ref_1 = g.add_ref("nzs_viewer_link")
  g.connect(nzs_viewer_link, nzs)

  nlh_viewer_link = g.add_link('nlh_viewer_link', "NLH Viewer")
  g.connect(nlh_viewer_link, nlh)

  done_link = g.add_link("done", "Done")
  done_ref_1 = g.add_ref("done")
  done_ref_2 = g.add_ref("done")
  done_ref_3 = g.add_ref("done")
  done_ref_4 = g.add_ref("done")

  back_link = g.add_link('back_link', 'Back to Project')
  g.connect(done_link, back_link)

  g.connect(hazard_type, done_ref_1, "Cancel", :BOXED)
  g.connect(user_def, done_ref_2, "Return to Project")
  g.connect(nzs, done_ref_3, "Return to Project")
  g.connect(nlh, done_ref_4, "Return to Project")

  nlh_ed_link = g.add_link("nlh_ed_link", "NLH Editor")
  nlh_ed_ref = g.add_ref("nlh_ed_link")
  g.connect(nlh, nlh_ed_link, "Edit", :BOXED)
  g.connect(nlh_ed_link, nlh_edit)
  g.connect(hazard_type, nlh_ed_ref)

  nzs_ed_link = g.add_link("nzs_ed_link", "NZS Editor")
  nzs_ed_ref = g.add_ref("nzs_ed_link")
  g.connect(nzs, nzs_ed_link, "Edit", :BOXED)
  g.connect(nzs_ed_link, nzs_edit)
  g.connect(hazard_type, nzs_ed_ref)

  interpolated_editor_link = g.add_link("interpolated_editor", "Interpolated Editor")
  interpolated_editor_ref_1 = g.add_ref("interpolated_editor")
  interpolated_editor_ref_2 = g.add_ref("interpolated_editor")
  g.connect(interpolated_editor_link, user_def_edit)
  g.connect(hazard_type, interpolated_editor_ref_1)

  g.connect(user_def, interpolated_editor_link, "Edit", :BOXED)

  g.connect(user_def_edit, user_def_import, "Import", :BOXED)
  g.connect(user_def_edit, start_ref_1, "Cancel", :BOXED)

  g.connect(type, user_def_viewer_link, "User-defined Hazard Curve")
  g.connect(type, nzs_viewer_link, "NZ Standard Curve")
  g.connect(type, nlh_viewer_link, "Non-Linear Hyperbolic")
  g.connect(start_link, exists)

  import_file = g.add_action("import", "Import File")
  g.connect(user_def_import, import_file, "Import", :BOXED)
  g.connect(import_file, user_def_import, "Error")

  save_1 = g.add_action("save_1", "Save to Database")
  save_2 = g.add_action("save_2", "Save to Database")
  save_3 = g.add_action("save_3", "Save to Database")

  g.connect(import_file, save_1, "Success")
  g.connect(user_def_edit, save_1, "Commit", :BOXED)
  g.connect(nzs_edit, save_2, "Commit", :BOXED)
  g.connect(nlh_edit, save_3, "Commit", :BOXED)
  g.connect(save_1, user_def_viewer_ref)

  g.connect(import_file, interpolated_editor_ref_2, "Cancel")
  browse = g.add_tool("browser", "File Browser")
  g.connect(import_file, browse, "Browse", :BOXED)
  g.connect(browse, import_file)

  g.connect(save_2, nzs_viewer_ref_1)
  g.connect(nzs_edit, start_ref_2, "Cancel", :BOXED)
  g.connect(nlh_edit, start_ref_3, "Cancel", :BOXED)
}
#puts(g.output( :none => String))
#g.output( :png => "pages-test2.png")
g.output( :pdf => "pages-test2.pdf")

#g.links.each_value {|v|
#  puts(v)
#}
