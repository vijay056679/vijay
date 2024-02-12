

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/UpdateNameServlet")
public class UpdateNameServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
       
    
    public UpdateNameServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
	int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
	
	PrintWriter pw=response.getWriter();
	 Connection con=null;
	 try
	 {
		 Class.forName("oracle.jdbc.driver.OracleDriver"); 
			String url="jdbc:oracle:thin:@localhost:1521:xe";
			 con=DriverManager.getConnection(url,"system","056679");
			 String sql="select * from Account where accountnumber=?";
			 PreparedStatement ps= con.prepareStatement(sql);
			 ps.setInt(1, accountnumber);
			 
			 ResultSet rs=ps.executeQuery();
			 if(rs.next())
			 {
				 pw.println("<html>");
				 pw.println("<body Style='background-color:gold'>");
				 pw.println("<center>");
				 pw.print("<from action='Update' method='Post'>");
				 pw.println("AccountNumber:");
				 pw.println(" <input type='text' value='"+rs.getInt(1)+"' + name='accountnumber'/>");
				 pw.println("<br><br>");
				 pw.println("Name:");
				 pw.println(" <input type='text' value='"+rs.getString(2)+"' + name='name'/>");
				 pw.println("<br><br>");
				 pw.println("Balance:");
				 pw.println(" <input type='text' value='"+rs.getInt(3)+"' + name='balance'/>");
				 pw.println("<br><br>");
				 pw.println(" <input type='submit' value='Update'/>");
				 pw.println(" </from>");
				 pw.println("</center>");
				 pw.println("</body>");
				 pw.println("</html>");
			 }
			 else
			 {
				 pw.println("Error: Invalid Account Number");
			 }
			
	 }
	 catch(Exception e)
	 {
		 pw.println("Exception:"+e.getMessage());
	 }
	 finally
	 {
		 if(con !=null)
		 {
			 try {
				con.close();
			} catch (SQLException e) {
				
				e.printStackTrace();
			}
		 }
	 }
	
	
	
	
	
	}
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException
	{
		int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
		String name=request.getParameter("name");
		int balance=Integer.parseInt(request.getParameter("balance"));
		
		PrintWriter pw=response.getWriter();
		 Connection con=null;
		 try
		 {
			 Class.forName("oracle.jdbc.driver.OracleDriver");
				String url="jdbc:oracle:thin:@localhost:1521:xe";
				 con=DriverManager.getConnection(url,"system","056679");
				 String sql1="update Account set name=? where accountnumber=?";
				 PreparedStatement ps1= con.prepareStatement(sql1);
				 ps1.setString(1, name);
				 ps1.setInt(2,accountnumber);
				 
				 int count=ps1.executeUpdate();
				 
				 if(count>0)
				 {
					 pw.println(" Record Updated successfully");
				 }
				 else
				 {
					 pw.println(" Failed in Insertion of Record");
				 }
	    }
		 catch(Exception e)
		 {
			 pw.println("Exception:"+e.getMessage());
		 }
		 finally
		 {
			 if(con != null)
			 {
				 try {
					con.close();
				} catch (SQLException e) {
					
					e.printStackTrace();
				}
			 }
		 }
		 

}
}
