

import java.io.IOException;
import java.io.PrintWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


@WebServlet("/AccountCreationServlet")
public class AccountCreationServlet extends HttpServlet {
	private static final long serialVersionUID = 1L;
       
  
    public AccountCreationServlet() {
        super();
        // TODO Auto-generated constructor stub
    }

	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException 
	{
		PrintWriter pw=response.getWriter();
		
		 int accountnumber=Integer.parseInt(request.getParameter("accountnumber"));
		 String name=request.getParameter("name");
		 int balance=Integer.parseInt(request.getParameter("balance"));
		 
		 Connection con=null;
		 try
		 {
			     Class.forName("oracle.jdbc.driver.OracleDriver");
				String url="jdbc:oracle:thin:@localhost:1521:xe";
				con=DriverManager.getConnection(url,"system","056679");
				
				String sql="insert into Account values(?,?,?)";
				
				PreparedStatement ps=con.prepareStatement(sql);
				
				ps.setInt(1, accountnumber);
				ps.setString(2, name);
				ps.setInt(3, balance);
				
				int count=ps.executeUpdate();
				if(count>0)
				{
					
					response.setContentType("text/html");
					RequestDispatcher rd=request.getRequestDispatcher("AccountCreation.html");
					rd.include(request, response);
				}
				else
				{
					pw.println("Failed to Insertion");
					response.setContentType("text/html");
					RequestDispatcher rd=request.getRequestDispatcher("insert_account_form");
					rd.include(request, response);
				}
		}
		 catch(Exception e)
		 {
			 e.printStackTrace();
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
